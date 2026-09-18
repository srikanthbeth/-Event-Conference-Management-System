import os
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "event_conference_management_test"
)

from fastapi.testclient import TestClient

from database import Base, SessionLocal, engine
from main import app

from models.attendee import Attendee
from models.event import Event
from models.payment import Payment
from models.purchase import Purchase
from models.registration import Registration
from models.ticket import Ticket
from models.user import User

from utils.enums import (
    EventStatus,
    EventType,
    PaymentMethod,
    PaymentStatus,
    RegistrationStatus,
    RefundStatus,
    TicketType,
    UserRole,
)

from utils.security import hash_password


client = TestClient(app)


def unique_email(prefix="refund"):
    return f"{prefix}_{uuid4().hex}@example.com"


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_user(
    role=UserRole.ATTENDEE,
    prefix="user",
):
    db = SessionLocal()

    email = unique_email(prefix)

    user = User(
        full_name="Test User",
        email=email,
        phone="9876543210",
        hashed_password=hash_password("Password@123"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id

    db.close()

    return user_id, email


def login(email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Password@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_event(
    organizer_id,
    start_date=None,
    status=EventStatus.REGISTRATION_OPEN,
):
    db = SessionLocal()

    now = datetime.utcnow()

    if start_date is None:
        start_date = now + timedelta(days=7)

    event = Event(
        event_name=f"Refund Event {uuid4().hex[:8]}",
        description="Refund test event",
        event_type=EventType.CONFERENCE,
        organizer_id=organizer_id,
        start_date=start_date,
        end_date=start_date + timedelta(hours=4),
        registration_start=now - timedelta(days=1),
        registration_end=start_date - timedelta(days=1),
        capacity=100,
        status=status,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    event_id = event.id

    db.close()

    return event_id


def create_attendee(email):
    db = SessionLocal()

    attendee = Attendee(
        full_name="Test Attendee",
        email=email,
        phone="9876543212",
        organization="Test Organization",
        designation="Developer",
    )

    db.add(attendee)
    db.commit()
    db.refresh(attendee)

    attendee_id = attendee.id

    db.close()

    return attendee_id


def create_purchase(
    attendee_id,
    event_id,
    amount=Decimal("1000.00"),
    payment_status=PaymentStatus.SUCCESSFUL,
):
    db = SessionLocal()

    ticket = Ticket(
        event_id=event_id,
        ticket_type=TicketType.STANDARD,
        price=amount,
        quantity=10,
        available_quantity=10,
        sale_start=datetime.utcnow() - timedelta(days=1),
        sale_end=datetime.utcnow() + timedelta(days=30),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    registration = Registration(
        attendee_id=attendee_id,
        event_id=event_id,
        registration_date=datetime.utcnow(),
        registration_status=RegistrationStatus.CONFIRMED,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    purchase = Purchase(
        registration_id=registration.id,
        ticket_id=ticket.id,
        quantity=1,
        subtotal=amount,
        discount=Decimal("0.00"),
        tax=Decimal("0.00"),
        total_amount=amount,
    )

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    payment = Payment(
        purchase_id=purchase.id,
        transaction_id=f"TXN-{uuid4().hex}",
        payment_method=PaymentMethod.UPI,
        amount=amount,
        payment_status=payment_status,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    purchase_id = purchase.id
    payment_id = payment.id
    registration_id = registration.id

    db.close()

    return purchase_id, payment_id, registration_id


def test_cancel_purchase_before_event_full_refund():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer",
    )

    attendee_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee",
    )

    event_id = create_event(
        organizer_id,
        start_date=datetime.utcnow() + timedelta(days=7),
    )

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    token = login(attendee_email)

    response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Unable to attend",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert Decimal(str(data["refund_amount"])) == Decimal("1000.00")
    assert data["refund_status"] == "Pending"
    assert data["cancellation_reason"] == "Unable to attend"


def test_cancel_purchase_near_event_partial_refund():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_near",
    )

    attendee_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_near",
    )

    event_id = create_event(
        organizer_id,
        start_date=datetime.utcnow() + timedelta(hours=24),
    )

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    token = login(attendee_email)

    response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Emergency",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert Decimal(str(data["refund_amount"])) == Decimal("500.00")


def test_cancel_purchase_after_event_rejected():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_after",
    )

    attendee_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_after",
    )

    event_id = create_event(
        organizer_id,
        start_date=datetime.utcnow() - timedelta(hours=2),
    )

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    token = login(attendee_email)

    response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Late cancellation",
        },
    )

    assert response.status_code == 400


def test_cancel_purchase_requires_authentication():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_auth",
    )

    attendee_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_auth",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        json={
            "reason": "No longer attending",
        },
    )

    assert response.status_code == 401


def test_attendee_cannot_cancel_other_attendees_purchase():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_owner",
    )

    _, owner_email = create_user(
        UserRole.ATTENDEE,
        "purchase_owner",
    )

    _, other_email = create_user(
        UserRole.ATTENDEE,
        "other_attendee",
    )

    event_id = create_event(organizer_id)

    owner_attendee_id = create_attendee(owner_email)

    purchase_id, _, _ = create_purchase(
        owner_attendee_id,
        event_id,
    )

    token = login(other_email)

    response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Trying another purchase",
        },
    )

    assert response.status_code == 403


def test_failed_payment_cannot_be_refunded():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_failed",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_failed",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
        payment_status=PaymentStatus.FAILED,
    )

    token = login(attendee_email)

    response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Failed payment test",
        },
    )

    assert response.status_code == 400


def test_duplicate_purchase_cancellation_rejected():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_duplicate",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_duplicate",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    token = login(attendee_email)

    first = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "First cancellation",
        },
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Second cancellation",
        },
    )

    assert second.status_code == 400


def test_get_refund():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_get",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_get",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    token = login(attendee_email)

    create_response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Need refund",
        },
    )

    assert create_response.status_code == 201

    refund_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/refunds/{refund_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == refund_id


def test_get_purchase_refund():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_purchase_refund",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_purchase_refund",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    token = login(attendee_email)

    create_response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Purchase refund",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        f"/api/v1/purchases/{purchase_id}/refund",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["purchase_id"] == purchase_id


def test_admin_can_complete_refund():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_complete",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_complete",
    )

    admin_id, admin_email = create_user(
        UserRole.ADMIN,
        "admin_complete",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    attendee_token = login(attendee_email)

    create_response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(attendee_token),
        json={
            "reason": "Complete refund test",
        },
    )

    assert create_response.status_code == 201

    refund_id = create_response.json()["id"]

    admin_token = login(admin_email)

    response = client.patch(
        f"/api/v1/refunds/{refund_id}/complete",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["refund_status"] == "Completed"
    assert data["refund_date"] is not None


def test_non_admin_cannot_complete_refund():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_nonadmin",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_nonadmin",
    )

    event_id = create_event(organizer_id)

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    attendee_token = login(attendee_email)

    create_response = client.post(
        f"/api/v1/purchases/{purchase_id}/cancel",
        headers=auth_headers(attendee_token),
        json={
            "reason": "Non admin completion",
        },
    )

    refund_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/refunds/{refund_id}/complete",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 403


def test_event_organizer_can_cancel_own_event():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "event_owner",
    )

    event_id = create_event(organizer_id)

    token = login(organizer_email)

    response = client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Event postponed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_status"] == "Cancelled"
    assert data["cancellation_reason"] == "Event postponed"


def test_organizer_cannot_cancel_other_organizers_event():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "event_owner_two",
    )

    other_id, other_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "event_other_owner",
    )

    event_id = create_event(organizer_id)

    token = login(other_email)

    response = client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Unauthorized cancellation",
        },
    )

    assert response.status_code == 403


def test_event_cancellation_creates_full_refund():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_event_refund",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_event_refund",
    )

    event_id = create_event(
        organizer_id,
        start_date=datetime.utcnow() + timedelta(days=7),
    )

    attendee_db_id = create_attendee(attendee_email)

    purchase_id, _, _ = create_purchase(
        attendee_db_id,
        event_id,
    )

    organizer_token = login(organizer_email)

    response = client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers=auth_headers(organizer_token),
        json={
            "reason": "Venue unavailable",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_status"] == "Cancelled"
    assert data["refunds_created"] == 1

    refund = data["refunds"][0]

    assert Decimal(
        str(refund["refund_amount"])
    ) == Decimal("1000.00")

    assert refund["refund_status"] == "Pending"


def test_admin_can_cancel_event():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_admin_cancel",
    )

    _, admin_email = create_user(
        UserRole.ADMIN,
        "admin_event_cancel",
    )

    event_id = create_event(organizer_id)

    token = login(admin_email)

    response = client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Administrative cancellation",
        },
    )

    assert response.status_code == 200

    assert response.json()["event_status"] == "Cancelled"


def test_attendee_cannot_cancel_event():
    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_attendee_event",
    )

    _, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_event_cancel",
    )

    event_id = create_event(organizer_id)

    token = login(attendee_email)

    response = client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers=auth_headers(token),
        json={
            "reason": "Attendee trying event cancellation",
        },
    )

    assert response.status_code == 403


def test_cancel_event_refunds_multiple_purchases():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_multiple",
    )

    _, attendee_email_1 = create_user(
        UserRole.ATTENDEE,
        "attendee_multiple_1",
    )

    _, attendee_email_2 = create_user(
        UserRole.ATTENDEE,
        "attendee_multiple_2",
    )

    event_id = create_event(organizer_id)

    attendee_id_1 = create_attendee(attendee_email_1)
    attendee_id_2 = create_attendee(attendee_email_2)

    create_purchase(
        attendee_id_1,
        event_id,
        Decimal("1000.00"),
    )

    create_purchase(
        attendee_id_2,
        event_id,
        Decimal("1500.00"),
    )

    organizer_token = login(organizer_email)

    response = client.post(
        f"/api/v1/events/{event_id}/cancel",
        headers=auth_headers(organizer_token),
        json={
            "reason": "Event cancelled",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["refunds_created"] == 2

    amounts = sorted(
        Decimal(str(refund["refund_amount"]))
        for refund in data["refunds"]
    )

    assert amounts == [
        Decimal("1000.00"),
        Decimal("1500.00"),
    ]