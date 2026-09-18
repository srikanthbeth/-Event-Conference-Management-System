import os
from datetime import datetime, timedelta
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "event_conference_management_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import select

from database import Base, SessionLocal, engine
from main import app
from models.user import User


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def register_user(
    role="Attendee",
    email=None,
):
    email = email or unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "phone": "9876543210",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code == 201

    return email


def login_user(
    email,
    password="Test@12345",
):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def get_user_id(email):
    db = SessionLocal()

    try:
        user = db.scalars(
            select(User).where(
                User.email == email
            )
        ).first()

        assert user is not None

        return user.id

    finally:
        db.close()


def create_organizer():
    email = register_user(
        "Event Organizer"
    )

    token = login_user(email)

    user_id = get_user_id(email)

    return email, token, user_id


def create_event(
    token,
    organizer_id,
    capacity=100,
    registration_start=None,
    registration_end=None,
    event_start=None,
    event_end=None,
):
    now = datetime.utcnow()

    event_start = event_start or (
        now + timedelta(days=5)
    )

    event_end = event_end or (
        event_start + timedelta(hours=8)
    )

    registration_start = registration_start or (
        now - timedelta(hours=1)
    )

    registration_end = registration_end or (
        now + timedelta(days=2)
    )

    payload = {
        "event_name": (
            f"Technology Conference "
            f"{uuid4().hex[:6]}"
        ),
        "description": (
            "Annual technology conference"
        ),
        "event_type": "Conference",
        "organizer_id": organizer_id,
        "start_date": event_start.isoformat(),
        "end_date": event_end.isoformat(),
        "registration_start": (
            registration_start.isoformat()
        ),
        "registration_end": (
            registration_end.isoformat()
        ),
        "capacity": capacity,
        "status": "Registration Open",
    }

    response = client.post(
        "/api/v1/events",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_attendee():
    email = register_user("Attendee")

    token = login_user(email)

    return email, token


def test_register_for_event():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
        capacity=100,
    )

    attendee_email, attendee_token = create_attendee()

    response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["event_id"] == event["id"]
    assert data["registration_status"] == "Pending"
    assert data["registration_date"] is not None
    assert data["attendee_id"] is not None


def test_registration_requires_authentication():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    response = client.post(
        f"/api/v1/events/{event['id']}/register"
    )

    assert response.status_code == 401


def test_non_attendee_cannot_register():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    speaker_email = register_user("Speaker")
    speaker_token = login_user(speaker_email)

    response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(speaker_token),
    )

    assert response.status_code == 403


def test_event_not_found():
    attendee_email, attendee_token = create_attendee()

    response = client.post(
        "/api/v1/events/999999/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 404


def test_duplicate_registration_is_rejected():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    attendee_email, attendee_token = create_attendee()

    first_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert second_response.status_code == 400

    assert "already registered" in (
        second_response.json()["detail"].lower()
    )


def test_registration_cannot_exceed_event_capacity():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
        capacity=1,
    )

    first_email, first_token = create_attendee()

    first_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(first_token),
    )

    assert first_response.status_code == 201

    second_email, second_token = create_attendee()

    second_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(second_token),
    )

    assert second_response.status_code == 400

    assert "capacity" in (
        second_response.json()["detail"].lower()
    )


def test_registration_before_registration_period_is_rejected():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    now = datetime.utcnow()

    event = create_event(
        organizer_token,
        organizer_id,
        registration_start=(
            now + timedelta(days=2)
        ),
        registration_end=(
            now + timedelta(days=3)
        ),
        event_start=(
            now + timedelta(days=5)
        ),
        event_end=(
            now + timedelta(days=5, hours=8)
        ),
    )

    attendee_email, attendee_token = create_attendee()

    response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 400

    assert "registration" in (
        response.json()["detail"].lower()
    )


def test_registration_after_registration_period_is_rejected():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    now = datetime.utcnow()

    event = create_event(
        organizer_token,
        organizer_id,
        registration_start=(
            now - timedelta(days=3)
        ),
        registration_end=(
            now - timedelta(days=1)
        ),
        event_start=(
            now + timedelta(days=5)
        ),
        event_end=(
            now + timedelta(days=5, hours=8)
        ),
    )

    attendee_email, attendee_token = create_attendee()

    response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 400

    assert "registration" in (
        response.json()["detail"].lower()
    )


def test_get_registrations():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    attendee_email, attendee_token = create_attendee()

    create_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/registrations"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_registration():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    attendee_email, attendee_token = create_attendee()

    create_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert create_response.status_code == 201

    registration_id = (
        create_response.json()["id"]
    )

    response = client.get(
        f"/api/v1/registrations/{registration_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == registration_id
    assert data["event_id"] == event["id"]


def test_registration_not_found():
    response = client.get(
        "/api/v1/registrations/999999"
    )

    assert response.status_code == 404


def test_cancel_registration():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    attendee_email, attendee_token = create_attendee()

    create_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert create_response.status_code == 201

    registration_id = (
        create_response.json()["id"]
    )

    response = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=auth_headers(attendee_token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == registration_id
    assert data["registration_status"] == "Cancelled"


def test_cancel_registration_requires_authentication():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    attendee_email, attendee_token = create_attendee()

    create_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert create_response.status_code == 201

    registration_id = (
        create_response.json()["id"]
    )

    response = client.post(
        f"/api/v1/registrations/{registration_id}/cancel"
    )

    assert response.status_code == 401


def test_attendee_cannot_cancel_another_attendees_registration():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    first_email, first_token = create_attendee()

    create_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(first_token),
    )

    assert create_response.status_code == 201

    registration_id = (
        create_response.json()["id"]
    )

    second_email, second_token = create_attendee()

    response = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 403


def test_cancel_registration_twice_is_rejected():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
    )

    attendee_email, attendee_token = create_attendee()

    create_response = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(attendee_token),
    )

    assert create_response.status_code == 201

    registration_id = (
        create_response.json()["id"]
    )

    first_cancel = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=auth_headers(attendee_token),
    )

    assert first_cancel.status_code == 200

    second_cancel = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=auth_headers(attendee_token),
    )

    assert second_cancel.status_code == 400

    assert "already cancelled" in (
        second_cancel.json()["detail"].lower()
    )


def test_cancelled_registration_frees_event_capacity():
    organizer_email, organizer_token, organizer_id = (
        create_organizer()
    )

    event = create_event(
        organizer_token,
        organizer_id,
        capacity=1,
    )

    first_email, first_token = create_attendee()

    first_registration = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(first_token),
    )

    assert first_registration.status_code == 201

    registration_id = (
        first_registration.json()["id"]
    )

    cancel_response = client.post(
        f"/api/v1/registrations/{registration_id}/cancel",
        headers=auth_headers(first_token),
    )

    assert cancel_response.status_code == 200

    second_email, second_token = create_attendee()

    second_registration = client.post(
        f"/api/v1/events/{event['id']}/register",
        headers=auth_headers(second_token),
    )

    assert second_registration.status_code == 201