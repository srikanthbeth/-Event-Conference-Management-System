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
from models.hall import Hall
from models.payment import Payment
from models.purchase import Purchase
from models.registration import Registration
from models.session import Session
from models.speaker import Speaker
from models.ticket import Ticket
from models.user import User
from models.venue import Venue

from utils.enums import (
    EventStatus,
    EventType,
    HallAvailabilityStatus,
    PaymentMethod,
    PaymentStatus,
    RegistrationStatus,
    TicketType,
    UserRole,
    VenueStatus,
)

from utils.security import hash_password


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix):
    return f"{prefix}_{uuid4().hex}@example.com"


def create_user(role, prefix):
    db = SessionLocal()

    user = User(
        full_name=prefix,
        email=unique_email(prefix),
        phone="9876543210",
        hashed_password=hash_password("Test@123"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    result = {
        "id": user.id,
        "email": user.email,
    }

    db.close()

    return result


def login(email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_data():
    db = SessionLocal()

    admin = User(
        full_name="Level 14 Admin",
        email=unique_email("admin14"),
        phone="9000000001",
        hashed_password=hash_password("Test@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )

    organizer = User(
        full_name="Level 14 Organizer",
        email=unique_email("organizer14"),
        phone="9000000002",
        hashed_password=hash_password("Test@123"),
        role=UserRole.EVENT_ORGANIZER,
        is_active=True,
    )

    attendee_user = User(
        full_name="Level 14 Attendee",
        email=unique_email("attendee14"),
        phone="9000000003",
        hashed_password=hash_password("Test@123"),
        role=UserRole.ATTENDEE,
        is_active=True,
    )

    db.add_all(
        [
            admin,
            organizer,
            attendee_user,
        ]
    )

    db.commit()

    db.refresh(admin)
    db.refresh(organizer)
    db.refresh(attendee_user)

    venue = Venue(
        venue_name="Level 14 Venue",
        address="Main Road",
        city="Hyderabad",
        capacity=1000,
        facilities="WiFi",
        status=VenueStatus.ACTIVE,
    )

    db.add(venue)
    db.commit()
    db.refresh(venue)

    hall = Hall(
        venue_id=venue.id,
        hall_name="Analytics Hall",
        capacity=500,
        floor=1,
        availability_status=HallAvailabilityStatus.AVAILABLE,
    )

    db.add(hall)
    db.commit()
    db.refresh(hall)

    now = datetime.utcnow()

    event1 = Event(
        event_name="Hyderabad Conference",
        description="Conference",
        event_type=EventType.CONFERENCE,
        organizer_id=organizer.id,
        start_date=now + timedelta(days=5),
        end_date=now + timedelta(days=6),
        registration_start=now - timedelta(days=5),
        registration_end=now + timedelta(days=3),
        capacity=100,
        status=EventStatus.REGISTRATION_OPEN,
    )

    event2 = Event(
        event_name="Bangalore Workshop",
        description="Workshop",
        event_type=EventType.WORKSHOP,
        organizer_id=organizer.id,
        start_date=now + timedelta(days=15),
        end_date=now + timedelta(days=16),
        registration_start=now - timedelta(days=5),
        registration_end=now + timedelta(days=10),
        capacity=50,
        status=EventStatus.PUBLISHED,
    )

    event3 = Event(
        event_name="Completed Seminar",
        description="Completed",
        event_type=EventType.SEMINAR,
        organizer_id=organizer.id,
        start_date=now - timedelta(days=20),
        end_date=now - timedelta(days=19),
        registration_start=now - timedelta(days=30),
        registration_end=now - timedelta(days=21),
        capacity=200,
        status=EventStatus.COMPLETED,
    )

    db.add_all(
        [
            event1,
            event2,
            event3,
        ]
    )

    db.commit()

    db.refresh(event1)
    db.refresh(event2)
    db.refresh(event3)

    attendee = Attendee(
        full_name="Level 14 Attendee",
        email=attendee_user.email,
        phone="9111111111",
        organization="Test Company",
        designation="Developer",
    )

    db.add(attendee)
    db.commit()
    db.refresh(attendee)

    registration = Registration(
        attendee_id=attendee.id,
        event_id=event1.id,
        registration_date=now,
        registration_status=RegistrationStatus.CONFIRMED,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    ticket = Ticket(
        event_id=event1.id,
        ticket_type=TicketType.STANDARD,
        price=Decimal("1000.00"),
        quantity=100,
        available_quantity=98,
        sale_start=now - timedelta(days=5),
        sale_end=now + timedelta(days=5),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    purchase = Purchase(
        registration_id=registration.id,
        ticket_id=ticket.id,
        quantity=2,
        subtotal=Decimal("2000.00"),
        discount=Decimal("0.00"),
        tax=Decimal("200.00"),
        total_amount=Decimal("2200.00"),
    )

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    payment = Payment(
        purchase_id=purchase.id,
        transaction_id=f"LEVEL14-{uuid4().hex}",
        payment_method=PaymentMethod.UPI,
        amount=Decimal("2200.00"),
        payment_status=PaymentStatus.SUCCESSFUL,
        payment_date=now,
    )

    db.add(payment)

    speaker = Speaker(
        name="Level 14 Speaker",
        email=unique_email("speaker14"),
        phone="9222222222",
        bio="Technology speaker",
        expertise="FastAPI",
        company="Test Company",
        experience=10,
        is_active=True,
    )

    db.add(speaker)
    db.commit()
    db.refresh(speaker)

    session1 = Session(
        event_id=event1.id,
        speaker_id=speaker.id,
        hall_id=hall.id,
        title="FastAPI Session",
        description="FastAPI",
        start_time=now + timedelta(days=5, hours=1),
        end_time=now + timedelta(days=5, hours=2),
        capacity=100,
        session_type="Workshop",
    )

    session2 = Session(
        event_id=event2.id,
        speaker_id=speaker.id,
        hall_id=hall.id,
        title="Python Session",
        description="Python",
        start_time=now + timedelta(days=15, hours=1),
        end_time=now + timedelta(days=15, hours=2),
        capacity=50,
        session_type="Seminar",
    )

    db.add_all(
        [
            session1,
            session2,
        ]
    )

    db.commit()

    result = {
        "admin_email": admin.email,
        "organizer_email": organizer.email,
        "attendee_email": attendee_user.email,
        "event1_id": event1.id,
        "event2_id": event2.id,
        "event3_id": event3.id,
        "speaker_id": speaker.id,
        "session1_id": session1.id,
        "session2_id": session2.id,
    }

    db.close()

    return result


# ============================================================
# EVENT FILTERING
# ============================================================

def test_event_filter_by_type():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "event_type": "Conference",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1
    assert all(
        item["event_type"] == "Conference"
        for item in body
    )


def test_event_filter_by_city():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "city": "Hyderabad",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1
    assert all(
        item["city"].lower() == "hyderabad"
        for item in body
    )


def test_event_filter_by_status():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "status": "Completed",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1
    assert all(
        item["status"] == "Completed"
        for item in body
    )


def test_event_filter_by_available_capacity():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "min_available_capacity": 90,
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1


def test_event_pagination():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "page": 1,
            "limit": 2,
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) <= 2


def test_event_sort_descending():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "sort_by": "event_name",
            "sort_order": "desc",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 2

    names = [
        item["event_name"]
        for item in body
    ]

    assert names == sorted(
        names,
        reverse=True,
    )


# ============================================================
# SESSION FILTERING
# ============================================================

def test_session_filter_by_speaker():
    data = create_data()

    response = client.get(
        "/api/v1/sessions",
        params={
            "speaker_id": data["speaker_id"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["speaker_id"] == data["speaker_id"]
        for item in body
    )


def test_session_filter_by_event():
    data = create_data()

    response = client.get(
        "/api/v1/sessions",
        params={
            "event_id": data["event1_id"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["event_id"] == data["event1_id"]
        for item in body
    )


def test_session_filter_by_type():
    data = create_data()

    response = client.get(
        "/api/v1/sessions",
        params={
            "session_type": "Workshop",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["session_type"] == "Workshop"
        for item in body
    )


def test_session_pagination():
    data = create_data()

    response = client.get(
        "/api/v1/sessions",
        params={
            "page": 1,
            "limit": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) <= 1


def test_session_sort_descending():
    data = create_data()

    response = client.get(
        "/api/v1/sessions",
        params={
            "sort_by": "title",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200

    body = response.json()

    titles = [
        item["title"]
        for item in body
    ]

    assert titles == sorted(
        titles,
        reverse=True,
    )


# ============================================================
# REGISTRATION FILTERING
# ============================================================

def test_registration_filter_by_event():
    data = create_data()

    response = client.get(
        "/api/v1/registrations",
        params={
            "event_id": data["event1_id"],
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["event_id"] == data["event1_id"]
        for item in body
    )


def test_registration_filter_by_status():
    data = create_data()

    response = client.get(
        "/api/v1/registrations",
        params={
            "status": "Confirmed",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["registration_status"]
        == "Confirmed"
        for item in body
    )


def test_registration_pagination():
    data = create_data()

    response = client.get(
        "/api/v1/registrations",
        params={
            "page": 1,
            "limit": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) <= 1


def test_registration_sorting():
    data = create_data()

    response = client.get(
        "/api/v1/registrations",
        params={
            "sort_by": "id",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200

    body = response.json()

    ids = [
        item["id"]
        for item in body
    ]

    assert ids == sorted(
        ids,
        reverse=True,
    )


# ============================================================
# PAYMENT FILTERING
# ============================================================

def test_payment_filter_by_status():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/payments",
        params={
            "payment_status": "Successful",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["payment_status"]
        == "Successful"
        for item in body
    )


def test_payment_filter_by_method():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/payments",
        params={
            "payment_method": "UPI",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert all(
        item["payment_method"] == "UPI"
        for item in body
    )


def test_payment_pagination():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/payments",
        params={
            "page": 1,
            "limit": 1,
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) <= 1


def test_payment_sorting():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_by": "amount",
            "sort_order": "desc",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1


# ============================================================
# INVALID PAGINATION
# ============================================================

def test_invalid_event_page():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "page": 0,
        },
        headers=headers(token),
    )

    assert response.status_code == 422


def test_invalid_event_limit():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/events",
        params={
            "limit": 0,
        },
        headers=headers(token),
    )

    assert response.status_code == 422


def test_invalid_session_page():
    response = client.get(
        "/api/v1/sessions",
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_invalid_payment_sort_order():
    data = create_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/payments",
        params={
            "sort_order": "wrong",
        },
        headers=headers(token),
    )

    assert response.status_code == 422