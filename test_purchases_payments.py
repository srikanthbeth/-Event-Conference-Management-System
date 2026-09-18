
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
from models.registration import Registration
from models.ticket import Ticket
from models.user import User

from utils.enums import (
    EventStatus,
    EventType,
    PaymentMethod,
    PaymentStatus,
    RegistrationStatus,
    TicketType,
    UserRole,
)
from utils.security import hash_password


client = TestClient(app)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ============================================================
# HELPERS
# ============================================================

def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex}@example.com"


def register_user(
    role=UserRole.ATTENDEE,
    prefix="user",
):
    email = unique_email(prefix)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {prefix}",
            "email": email,
            "phone": "9876543210",
            "password": "Test@12345",
            "role": role.value,
        },
    )

    assert response.status_code in (200, 201), response.text

    return email


def login_user(email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    return data["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def get_user_by_email(email):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        assert user is not None

        return user
    finally:
        db.close()


def create_organizer():
    email = register_user(
        role=UserRole.EVENT_ORGANIZER,
        prefix="organizer",
    )

    token = login_user(email)

    user = get_user_by_email(email)

    return user.id, email, token


def create_attendee():
    email = register_user(
        role=UserRole.ATTENDEE,
        prefix="attendee",
    )

    token = login_user(email)

    user = get_user_by_email(email)

    return user.id, email, token


def create_event():
    organizer_id, organizer_email, organizer_token = create_organizer()

    now = datetime.utcnow()

    event = Event(
        event_name=f"Level 8 Event {uuid4().hex[:8]}",
        description="Event for purchase and payment tests",
        event_type=EventType.CONFERENCE,
        organizer_id=organizer_id,
        start_date=now + timedelta(days=5),
        end_date=now + timedelta(days=6),
        registration_start=now - timedelta(days=1),
        registration_end=now + timedelta(days=4),
        capacity=100,
        status=EventStatus.REGISTRATION_OPEN,
    )

    db = SessionLocal()

    try:
        db.add(event)
        db.commit()
        db.refresh(event)

        return event.id, organizer_token
    finally:
        db.close()


def create_registration(
    event_id,
    attendee_id,
    status=RegistrationStatus.PENDING,
):
    db = SessionLocal()

    try:
        attendee = (
            db.query(Attendee)
            .filter(Attendee.id == attendee_id)
            .first()
        )

        if attendee is None:
            user = (
                db.query(User)
                .filter(User.id == attendee_id)
                .first()
            )

            attendee = Attendee(
                full_name=user.full_name,
                email=user.email,
                phone=user.phone,
                organization="Test Organization",
                designation="Test Attendee",
            )

            db.add(attendee)
            db.flush()

        registration = Registration(
            attendee_id=attendee.id,
            event_id=event_id,
            registration_date=datetime.utcnow(),
            registration_status=status,
        )

        db.add(registration)
        db.commit()
        db.refresh(registration)

        return registration.id

    finally:
        db.close()


def create_ticket(
    event_id,
    price=Decimal("100.00"),
    quantity=10,
    available_quantity=10,
    sale_start=None,
    sale_end=None,
):
    now = datetime.utcnow()

    if sale_start is None:
        sale_start = now - timedelta(hours=1)

    if sale_end is None:
        sale_end = now + timedelta(hours=1)

    db = SessionLocal()

    try:
        ticket = Ticket(
            event_id=event_id,
            ticket_type=TicketType.STANDARD,
            price=price,
            quantity=quantity,
            available_quantity=available_quantity,
            sale_start=sale_start,
            sale_end=sale_end,
        )

        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        return ticket.id

    finally:
        db.close()


def setup_purchase_data():
    event_id, organizer_token = create_event()

    attendee_id, attendee_email, attendee_token = create_attendee()

    registration_id = create_registration(
        event_id=event_id,
        attendee_id=attendee_id,
    )

    ticket_id = create_ticket(
        event_id=event_id,
        price=Decimal("100.00"),
        quantity=10,
        available_quantity=10,
    )

    return {
        "event_id": event_id,
        "attendee_id": attendee_id,
        "attendee_email": attendee_email,
        "attendee_token": attendee_token,
        "organizer_token": organizer_token,
        "registration_id": registration_id,
        "ticket_id": ticket_id,
    }


def purchase_payload(
    registration_id,
    quantity=2,
    discount="0.00",
    tax="0.00",
):
    return {
        "registration_id": registration_id,
        "quantity": quantity,
        "discount": discount,
        "tax": tax,
    }


def create_purchase(data, quantity=2):
    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            registration_id=data["registration_id"],
            quantity=quantity,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201, response.text

    return response.json()


def payment_payload(
    amount="200.00",
    transaction_id=None,
    payment_method=PaymentMethod.UPI,
    payment_status=PaymentStatus.SUCCESSFUL,
):
    if transaction_id is None:
        transaction_id = f"TXN-{uuid4().hex}"

    return {
        "transaction_id": transaction_id,
        "payment_method": payment_method.value,
        "amount": amount,
        "payment_status": payment_status.value,
    }


# ============================================================
# PURCHASE TESTS
# ============================================================

def test_successful_ticket_purchase():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=2,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["registration_id"] == data["registration_id"]
    assert body["ticket_id"] == data["ticket_id"]
    assert body["quantity"] == 2
    assert Decimal(body["subtotal"]) == Decimal("200.00")
    assert Decimal(body["discount"]) == Decimal("0.00")
    assert Decimal(body["tax"]) == Decimal("0.00")
    assert Decimal(body["total_amount"]) == Decimal("200.00")


def test_purchase_requires_authentication():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
    )

    assert response.status_code == 401


def test_non_attendee_cannot_purchase_ticket():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
        headers=auth_headers(data["organizer_token"]),
    )

    assert response.status_code == 403


def test_purchase_ticket_not_found():
    data = setup_purchase_data()

    response = client.post(
        "/api/v1/tickets/999999/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_purchase_registration_not_found():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            registration_id=999999,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_attendee_cannot_purchase_for_another_attendee():
    data = setup_purchase_data()

    other_attendee_id, other_email, other_token = create_attendee()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403


def test_cancelled_registration_cannot_purchase():
    data = setup_purchase_data()

    db = SessionLocal()

    try:
        registration = (
            db.query(Registration)
            .filter(
                Registration.id == data["registration_id"]
            )
            .first()
        )

        registration.registration_status = (
            RegistrationStatus.CANCELLED
        )

        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_ticket_event_must_match_registration_event():
    data = setup_purchase_data()

    other_event_id, _ = create_event()

    other_ticket_id = create_ticket(
        event_id=other_event_id,
        price=Decimal("100.00"),
        quantity=10,
        available_quantity=10,
    )

    response = client.post(
        f"/api/v1/tickets/{other_ticket_id}/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_ticket_outside_sale_period_cannot_be_purchased():
    data = setup_purchase_data()

    now = datetime.utcnow()

    db = SessionLocal()

    try:
        ticket = (
            db.query(Ticket)
            .filter(Ticket.id == data["ticket_id"])
            .first()
        )

        ticket.sale_start = now - timedelta(days=2)
        ticket.sale_end = now - timedelta(days=1)

        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_insufficient_ticket_quantity():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=11,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_purchase_quantity_must_be_positive():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=0,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 422


def test_negative_discount_is_rejected():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=2,
            discount="-10.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 422


def test_negative_tax_is_rejected():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=2,
            tax="-10.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 422


def test_discount_cannot_exceed_subtotal():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=2,
            discount="250.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_purchase_total_is_calculated_correctly():
    data = setup_purchase_data()

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=2,
            discount="20.00",
            tax="10.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert Decimal(body["subtotal"]) == Decimal("200.00")
    assert Decimal(body["discount"]) == Decimal("20.00")
    assert Decimal(body["tax"]) == Decimal("10.00")
    assert Decimal(body["total_amount"]) == Decimal("190.00")


def test_purchase_reduces_available_ticket_quantity():
    data = setup_purchase_data()

    create_purchase(
        data,
        quantity=3,
    )

    db = SessionLocal()

    try:
        ticket = (
            db.query(Ticket)
            .filter(Ticket.id == data["ticket_id"])
            .first()
        )

        assert ticket.available_quantity == 7

    finally:
        db.close()


def test_duplicate_purchase_is_rejected():
    data = setup_purchase_data()

    create_purchase(
        data,
        quantity=2,
    )

    response = client.post(
        f"/api/v1/tickets/{data['ticket_id']}/purchase",
        json=purchase_payload(
            data["registration_id"],
            quantity=1,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_get_purchase():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.get(
        f"/api/v1/purchases/{purchase['id']}",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == purchase["id"]
    assert body["registration_id"] == data["registration_id"]
    assert body["ticket_id"] == data["ticket_id"]


def test_get_purchase_not_found():
    data = setup_purchase_data()

    response = client.get(
        "/api/v1/purchases/999999",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_get_purchase_requires_authentication():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.get(
        f"/api/v1/purchases/{purchase['id']}",
    )

    assert response.status_code == 401


# ============================================================
# PAYMENT TESTS
# ============================================================

def test_successful_payment():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
            payment_status=PaymentStatus.SUCCESSFUL,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["purchase_id"] == purchase["id"]
    assert body["payment_status"] == PaymentStatus.SUCCESSFUL.value
    assert Decimal(body["amount"]) == Decimal("200.00")


def test_payment_requires_authentication():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
        ),
    )

    assert response.status_code == 401


def test_payment_purchase_not_found():
    data = setup_purchase_data()

    response = client.post(
        "/api/v1/payments/999999",
        json=payment_payload(
            amount="200.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_payment_amount_must_match_purchase():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="199.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_duplicate_transaction_id_is_rejected():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    transaction_id = f"DUP-{uuid4().hex}"

    first_response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
            transaction_id=transaction_id,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert first_response.status_code == 201

    data2 = setup_purchase_data()

    purchase2 = create_purchase(data2)

    second_response = client.post(
        f"/api/v1/payments/{purchase2['id']}",
        json=payment_payload(
            amount="200.00",
            transaction_id=transaction_id,
        ),
        headers=auth_headers(data2["attendee_token"]),
    )

    assert second_response.status_code == 400


def test_duplicate_payment_for_same_purchase_is_rejected():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    first_response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert second_response.status_code == 400


def test_failed_payment_does_not_confirm_registration():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
            payment_status=PaymentStatus.FAILED,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201

    db = SessionLocal()

    try:
        registration = (
            db.query(Registration)
            .filter(
                Registration.id == data["registration_id"]
            )
            .first()
        )

        assert (
            registration.registration_status
            == RegistrationStatus.PENDING
        )

    finally:
        db.close()


def test_successful_payment_confirms_registration():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
            payment_status=PaymentStatus.SUCCESSFUL,
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201

    db = SessionLocal()

    try:
        registration = (
            db.query(Registration)
            .filter(
                Registration.id == data["registration_id"]
            )
            .first()
        )

        assert (
            registration.registration_status
            == RegistrationStatus.CONFIRMED
        )

    finally:
        db.close()


def test_get_payment():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    payment_response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert payment_response.status_code == 201

    payment = payment_response.json()

    response = client.get(
        f"/api/v1/payments/{payment['id']}",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == payment["id"]
    assert body["purchase_id"] == purchase["id"]


def test_get_payment_not_found():
    data = setup_purchase_data()

    response = client.get(
        "/api/v1/payments/999999",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_get_payment_requires_authentication():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    payment_response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
        ),
        headers=auth_headers(data["attendee_token"]),
    )

    assert payment_response.status_code == 201

    payment = payment_response.json()

    response = client.get(
        f"/api/v1/payments/{payment['id']}",
    )

    assert response.status_code == 401


def test_other_attendee_cannot_pay_for_purchase():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    _, _, other_token = create_attendee()

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json=payment_payload(
            amount="200.00",
        ),
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403


def test_invalid_payment_amount_is_rejected():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json={
            "transaction_id": f"TXN-{uuid4().hex}",
            "payment_method": PaymentMethod.UPI.value,
            "amount": "0",
            "payment_status": PaymentStatus.SUCCESSFUL.value,
        },
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 400


def test_invalid_payment_method_is_rejected():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json={
            "transaction_id": f"TXN-{uuid4().hex}",
            "payment_method": "Bitcoin",
            "amount": "200.00",
            "payment_status": PaymentStatus.SUCCESSFUL.value,
        },
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 422


def test_payment_transaction_id_cannot_be_blank():
    data = setup_purchase_data()

    purchase = create_purchase(data)

    response = client.post(
        f"/api/v1/payments/{purchase['id']}",
        json={
            "transaction_id": "",
            "payment_method": PaymentMethod.UPI.value,
            "amount": "200.00",
            "payment_status": PaymentStatus.SUCCESSFUL.value,
        },
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 422
