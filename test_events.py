import os
from datetime import datetime, timedelta
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "event_conference_management_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app
from models.user import User
from utils.enums import UserRole
from utils.security import hash_password


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="event"):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_user(
    role=UserRole.EVENT_ORGANIZER.value,
):
    email = unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {role}",
            "email": email,
            "phone": "9876543210",
            "password": "Test@123",
            "role": role,
        },
    )

    assert response.status_code == 201

    return email


def login_user(email):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_event_payload():
    now = datetime.utcnow()

    return {
        "event_name": "FastAPI Conference",
        "description": "Advanced FastAPI Conference",
        "event_type": "Conference",
        "start_date": (
            now + timedelta(days=10)
        ).isoformat(),
        "end_date": (
            now + timedelta(days=12)
        ).isoformat(),
        "registration_start": (
            now + timedelta(days=1)
        ).isoformat(),
        "registration_end": (
            now + timedelta(days=9)
        ).isoformat(),
        "capacity": 500,
        "status": "Draft",
    }


def test_create_event():
    email = register_user()
    token = login_user(email)

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["event_name"] == "FastAPI Conference"
    assert data["event_type"] == "Conference"
    assert data["status"] == "Draft"
    assert data["capacity"] == 500
    assert data["organizer_id"] > 0


def test_event_requires_authentication():
    response = client.post(
        "/api/v1/events",
        json=create_event_payload(),
    )

    assert response.status_code == 401


def test_attendee_cannot_create_event():
    email = register_user(
        UserRole.ATTENDEE.value
    )

    token = login_user(email)

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    assert response.status_code == 403


def test_admin_can_create_event():
    email = register_user(
        UserRole.ADMIN.value
    )

    token = login_user(email)

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    assert response.status_code == 201


def test_list_events():
    email = register_user()
    token = login_user(email)

    client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    response = client.get(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_get_event():
    email = register_user()
    token = login_user(email)

    create_response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    event_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == event_id


def test_event_not_found():
    email = register_user()
    token = login_user(email)

    response = client.get(
        "/api/v1/events/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_update_event():
    email = register_user()
    token = login_user(email)

    create_response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    event_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "event_name": "Updated FastAPI Conference",
            "capacity": 750,
        },
    )

    assert response.status_code == 200
    assert response.json()["event_name"] == (
        "Updated FastAPI Conference"
    )
    assert response.json()["capacity"] == 750


def test_organizer_cannot_update_another_organizers_event():
    email1 = register_user()
    token1 = login_user(email1)

    create_response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token1}"
        },
        json=create_event_payload(),
    )

    event_id = create_response.json()["id"]

    email2 = register_user()
    token2 = login_user(email2)

    response = client.put(
        f"/api/v1/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token2}"
        },
        json={
            "event_name": "Unauthorized Update"
        },
    )

    assert response.status_code == 403


def test_delete_event():
    email = register_user()
    token = login_user(email)

    create_response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=create_event_payload(),
    )

    event_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert get_response.status_code == 404


def test_capacity_must_be_positive():
    email = register_user()
    token = login_user(email)

    payload = create_event_payload()
    payload["capacity"] = 0

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422

def test_event_end_must_be_after_start():
    email = register_user()
    token = login_user(email)

    now = datetime.utcnow()

    payload = create_event_payload()

    payload["start_date"] = (
        now + timedelta(days=12)
    ).isoformat()

    payload["end_date"] = (
        now + timedelta(days=10)
    ).isoformat()

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422

def test_registration_end_cannot_be_after_event_start():
    email = register_user()
    token = login_user(email)

    now = datetime.utcnow()

    payload = create_event_payload()

    payload["start_date"] = (
        now + timedelta(days=10)
    ).isoformat()

    payload["registration_end"] = (
        now + timedelta(days=11)
    ).isoformat()

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422
def test_registration_end_must_be_after_registration_start():
    email = register_user()
    token = login_user(email)

    now = datetime.utcnow()

    payload = create_event_payload()

    payload["registration_start"] = (
        now + timedelta(days=9)
    ).isoformat()

    payload["registration_end"] = (
        now + timedelta(days=5)
    ).isoformat()

    response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_cancelled_event_cannot_be_opened_for_registration():
    email = register_user()
    token = login_user(email)

    payload = create_event_payload()

    payload["status"] = "Cancelled"

    create_response = client.post(
        "/api/v1/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert create_response.status_code == 201

    event_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/events/{event_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Registration Open"
        },
    )

    assert response.status_code == 400