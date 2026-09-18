
import os
from datetime import datetime, timedelta
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
from models.session import Session as EventSession
from models.session_booking import SessionBooking
from models.speaker import Speaker
from models.user import User
from models.venue import Venue
from models.hall import Hall

from utils.enums import (
    EventStatus,
    EventType,
    HallAvailabilityStatus,
    RegistrationStatus,
    UserRole,
)


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

    return response.json()["access_token"]


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


def create_admin():
    email = register_user(
        role=UserRole.ADMIN,
        prefix="admin",
    )

    token = login_user(email)
    user = get_user_by_email(email)

    return user.id, email, token


def create_event(
    organizer_id,
    status=EventStatus.REGISTRATION_OPEN,
):
    now = datetime.utcnow()

    db = SessionLocal()

    try:
        event = Event(
            event_name=f"Level 9 Event {uuid4().hex[:8]}",
            description="Event for session booking tests",
            event_type=EventType.CONFERENCE,
            organizer_id=organizer_id,
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=6),
            registration_start=now - timedelta(days=1),
            registration_end=now + timedelta(days=4),
            capacity=100,
            status=status,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event.id

    finally:
        db.close()


def create_attendee_profile(user_id):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        attendee = (
            db.query(Attendee)
            .filter(
                Attendee.email == user.email,
            )
            .first()
        )

        if attendee:
            return attendee.id

        attendee = Attendee(
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            organization="Test Organization",
            designation="Test Attendee",
        )

        db.add(attendee)
        db.commit()
        db.refresh(attendee)

        return attendee.id

    finally:
        db.close()


def create_registration(
    attendee_id,
    event_id,
    registration_status=RegistrationStatus.CONFIRMED,
):
    db = SessionLocal()

    try:
        registration = Registration(
            attendee_id=attendee_id,
            event_id=event_id,
            registration_date=datetime.utcnow(),
            registration_status=registration_status,
        )

        db.add(registration)
        db.commit()
        db.refresh(registration)

        return registration.id

    finally:
        db.close()


def create_speaker():
    db = SessionLocal()

    try:
        speaker = Speaker(
            name=f"Speaker {uuid4().hex[:8]}",
            email=unique_email("speaker"),
            phone="9876543210",
            bio="Session booking test speaker",
            expertise="Technology",
            company="Test Company",
            experience=10,
            is_active=True,
        )

        db.add(speaker)
        db.commit()
        db.refresh(speaker)

        return speaker.id

    finally:
        db.close()


def create_venue_and_hall():
    db = SessionLocal()

    try:
        venue = Venue(
            venue_name=f"Venue {uuid4().hex[:8]}",
            address="Test Address",
            city="Tirupati",
            capacity=500,
            facilities="WiFi, Projector",
        )

        db.add(venue)
        db.flush()

        hall = Hall(
            venue_id=venue.id,
            hall_name=f"Hall {uuid4().hex[:8]}",
            capacity=100,
            floor=1,
            availability_status=HallAvailabilityStatus.AVAILABLE,
        )

        db.add(hall)
        db.commit()
        db.refresh(hall)

        return venue.id, hall.id

    finally:
        db.close()


def create_session(
    event_id,
    capacity=10,
):
    speaker_id = create_speaker()
    venue_id, hall_id = create_venue_and_hall()

    now = datetime.utcnow()

    db = SessionLocal()

    try:
        event_session = EventSession(
            event_id=event_id,
            speaker_id=speaker_id,
            hall_id=hall_id,
            title=f"Session {uuid4().hex[:8]}",
            description="Session booking test session",
            start_time=now + timedelta(days=5, hours=1),
            end_time=now + timedelta(days=5, hours=2),
            capacity=capacity,
            session_type="Workshop",
        )

        db.add(event_session)
        db.commit()
        db.refresh(event_session)

        return event_session.id

    finally:
        db.close()


def setup_booking_data(
    registration_status=RegistrationStatus.CONFIRMED,
    session_capacity=10,
):
    organizer_id, organizer_email, organizer_token = create_organizer()

    event_id = create_event(
        organizer_id=organizer_id,
    )

    attendee_id, attendee_email, attendee_token = create_attendee()

    attendee_profile_id = create_attendee_profile(
        attendee_id,
    )

    registration_id = create_registration(
        attendee_id=attendee_profile_id,
        event_id=event_id,
        registration_status=registration_status,
    )

    session_id = create_session(
        event_id=event_id,
        capacity=session_capacity,
    )

    return {
        "organizer_id": organizer_id,
        "organizer_token": organizer_token,
        "event_id": event_id,
        "attendee_user_id": attendee_id,
        "attendee_id": attendee_profile_id,
        "attendee_email": attendee_email,
        "attendee_token": attendee_token,
        "registration_id": registration_id,
        "session_id": session_id,
    }


def create_booking(data):
    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201, response.text

    return response.json()


# ============================================================
# BOOKING TESTS
# ============================================================

def test_confirmed_attendee_can_book_session():
    data = setup_booking_data()

    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["attendee_id"] == data["attendee_id"]
    assert body["session_id"] == data["session_id"]
    assert body["booking_status"] == "Booked"
    assert "booking_date" in body


def test_booking_requires_authentication():
    data = setup_booking_data()

    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
    )

    assert response.status_code == 401


def test_non_attendee_cannot_book_session():
    data = setup_booking_data()

    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["organizer_token"]),
    )

    assert response.status_code == 403


def test_session_not_found():
    data = setup_booking_data()

    response = client.post(
        "/api/v1/sessions/999999/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_unregistered_attendee_cannot_book_session():
    organizer_id, _, organizer_token = create_organizer()

    event_id = create_event(
        organizer_id=organizer_id,
    )

    attendee_id, _, attendee_token = create_attendee()

    create_attendee_profile(attendee_id)

    session_id = create_session(
        event_id=event_id,
    )

    response = client.post(
        f"/api/v1/sessions/{session_id}/book",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 403


def test_pending_attendee_cannot_book_session():
    data = setup_booking_data(
        registration_status=RegistrationStatus.PENDING,
    )

    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 403


def test_cancelled_attendee_cannot_book_session():
    data = setup_booking_data(
        registration_status=RegistrationStatus.CANCELLED,
    )

    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 403


def test_duplicate_session_booking_is_rejected():
    data = setup_booking_data()

    first_response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert second_response.status_code == 400


def test_session_capacity_cannot_be_exceeded():
    data = setup_booking_data(
        session_capacity=1,
    )

    first_response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert first_response.status_code == 201

    organizer_id, _, _ = create_organizer()

    # Create another attendee for the same event.
    second_attendee_user_id, _, second_attendee_token = (
        create_attendee()
    )

    second_attendee_id = create_attendee_profile(
        second_attendee_user_id,
    )

    create_registration(
        attendee_id=second_attendee_id,
        event_id=data["event_id"],
        registration_status=RegistrationStatus.CONFIRMED,
    )

    second_response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(second_attendee_token),
    )

    assert second_response.status_code == 400


def test_get_attendee_sessions():
    data = setup_booking_data()

    booking = create_booking(data)

    response = client.get(
        f"/api/v1/attendees/{data['attendee_id']}/sessions",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == booking["id"]
    assert body[0]["session_id"] == data["session_id"]
    assert body[0]["attendee_id"] == data["attendee_id"]


def test_get_attendee_sessions_returns_empty_list_when_no_booking():
    data = setup_booking_data()

    response = client.get(
        f"/api/v1/attendees/{data['attendee_id']}/sessions",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 200

    assert response.json() == []


def test_attendee_cannot_view_another_attendees_sessions():
    data = setup_booking_data()

    create_booking(data)

    other_attendee_user_id, _, other_token = create_attendee()

    other_attendee_id = create_attendee_profile(
        other_attendee_user_id,
    )

    response = client.get(
        f"/api/v1/attendees/{other_attendee_id}/sessions",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 403


def test_get_attendee_sessions_requires_authentication():
    data = setup_booking_data()

    response = client.get(
        f"/api/v1/attendees/{data['attendee_id']}/sessions",
    )

    assert response.status_code == 401


def test_get_nonexistent_attendee_sessions():
    data = setup_booking_data()

    response = client.get(
        "/api/v1/attendees/999999/sessions",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_delete_session_booking():
    data = setup_booking_data()

    booking = create_booking(data)

    response = client.delete(
        f"/api/v1/session-bookings/{booking['id']}",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert "message" in body


def test_delete_session_booking_requires_authentication():
    data = setup_booking_data()

    booking = create_booking(data)

    response = client.delete(
        f"/api/v1/session-bookings/{booking['id']}",
    )

    assert response.status_code == 401


def test_non_owner_cannot_delete_session_booking():
    data = setup_booking_data()

    booking = create_booking(data)

    other_attendee_user_id, _, other_token = create_attendee()

    create_attendee_profile(
        other_attendee_user_id,
    )

    response = client.delete(
        f"/api/v1/session-bookings/{booking['id']}",
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403


def test_delete_nonexistent_session_booking():
    data = setup_booking_data()

    response = client.delete(
        "/api/v1/session-bookings/999999",
        headers=auth_headers(data["attendee_token"]),
    )

    assert response.status_code == 404


def test_deleted_booking_frees_session_capacity():
    data = setup_booking_data(
        session_capacity=1,
    )

    booking = create_booking(data)

    delete_response = client.delete(
        f"/api/v1/session-bookings/{booking['id']}",
        headers=auth_headers(data["attendee_token"]),
    )

    assert delete_response.status_code == 200

    # Create another attendee.
    second_user_id, _, second_token = create_attendee()

    second_attendee_id = create_attendee_profile(
        second_user_id,
    )

    create_registration(
        attendee_id=second_attendee_id,
        event_id=data["event_id"],
        registration_status=RegistrationStatus.CONFIRMED,
    )

    response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 201, response.text


def test_attendee_can_rebook_after_booking_is_deleted():
    data = setup_booking_data()

    first_booking = create_booking(data)

    delete_response = client.delete(
        f"/api/v1/session-bookings/{first_booking['id']}",
        headers=auth_headers(data["attendee_token"]),
    )

    assert delete_response.status_code == 200

    second_response = client.post(
        f"/api/v1/sessions/{data['session_id']}/book",
        headers=auth_headers(data["attendee_token"]),
    )

    assert second_response.status_code == 201, second_response.text

    second_booking = second_response.json()

    assert second_booking["session_id"] == data["session_id"]
    assert second_booking["attendee_id"] == data["attendee_id"]


def test_admin_can_view_attendee_sessions():
    data = setup_booking_data()

    create_booking(data)

    _, _, admin_token = create_admin()

    response = client.get(
        f"/api/v1/attendees/{data['attendee_id']}/sessions",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["session_id"] == data["session_id"]


def test_admin_can_delete_session_booking():
    data = setup_booking_data()

    booking = create_booking(data)

    _, _, admin_token = create_admin()

    response = client.delete(
        f"/api/v1/session-bookings/{booking['id']}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200

