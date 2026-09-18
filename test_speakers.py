
import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "event_conference_management_test"
)

from fastapi.testclient import TestClient

from database import Base, engine
from main import app


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:10]}@example.com"


def register_user(role="Attendee", email=None):
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


def login_user(email, password="Test@12345"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def speaker_payload(email=None):
    return {
        "name": "John Smith",
        "email": email or unique_email("speaker"),
        "phone": "9876543210",
        "bio": "Technology conference speaker",
        "expertise": "Artificial Intelligence",
        "company": "Tech Solutions",
        "experience": 10,
    }


def create_speaker(token, email=None):
    return client.post(
        "/api/v1/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=speaker_payload(email),
    )


def test_create_speaker():
    email = register_user("Event Organizer")
    token = login_user(email)

    response = create_speaker(token)

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "John Smith"
    assert data["email"]
    assert data["expertise"] == "Artificial Intelligence"
    assert data["company"] == "Tech Solutions"
    assert data["experience"] == 10
    assert data["is_active"] is True


def test_create_speaker_requires_authentication():
    response = client.post(
        "/api/v1/speakers",
        json=speaker_payload(),
    )

    assert response.status_code == 401


def test_attendee_cannot_create_speaker():
    email = register_user("Attendee")
    token = login_user(email)

    response = create_speaker(token)

    assert response.status_code == 403


def test_admin_can_create_speaker():
    email = register_user("Admin")
    token = login_user(email)

    response = create_speaker(token)

    assert response.status_code == 201


def test_get_speakers():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/speakers"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_speaker():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/speakers/{speaker_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == speaker_id
    assert data["name"] == "John Smith"


def test_speaker_not_found():
    response = client.get(
        "/api/v1/speakers/999999"
    )

    assert response.status_code == 404


def test_update_speaker():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Updated Speaker",
            "phone": "9999999999",
            "bio": "Updated speaker biography",
            "expertise": "Cloud Computing",
            "company": "Updated Company",
            "experience": 15,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == speaker_id
    assert data["name"] == "Updated Speaker"
    assert data["phone"] == "9999999999"
    assert data["expertise"] == "Cloud Computing"
    assert data["company"] == "Updated Company"
    assert data["experience"] == 15


def test_update_speaker_requires_authentication():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        json={
            "name": "Updated Speaker"
        },
    )

    assert response.status_code == 401


def test_attendee_cannot_update_speaker():
    organizer_email = register_user("Event Organizer")
    organizer_token = login_user(organizer_email)

    create_response = create_speaker(organizer_token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    attendee_email = register_user("Attendee")
    attendee_token = login_user(attendee_email)

    response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {attendee_token}"
        },
        json={
            "name": "Unauthorized Update"
        },
    )

    assert response.status_code == 403


def test_duplicate_speaker_email():
    email = register_user("Event Organizer")
    token = login_user(email)

    speaker_email = unique_email("duplicate")

    first_response = create_speaker(
        token,
        speaker_email,
    )

    assert first_response.status_code == 201

    second_response = create_speaker(
        token,
        speaker_email,
    )

    assert second_response.status_code == 400

    assert (
        "already exists"
        in second_response.json()["detail"].lower()
    )


def test_negative_experience_is_rejected():
    email = register_user("Event Organizer")
    token = login_user(email)

    payload = speaker_payload()
    payload["experience"] = -1

    response = client.post(
        "/api/v1/speakers",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert response.status_code == 422


def test_inactive_speaker_can_be_deactivated():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "is_active": False
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == speaker_id
    assert data["is_active"] is False


def test_reactivate_speaker():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    deactivate_response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "is_active": False
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["is_active"] is False

    activate_response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "is_active": True
        },
    )

    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True


def test_update_speaker_email():
    email = register_user("Event Organizer")
    token = login_user(email)

    create_response = create_speaker(token)

    assert create_response.status_code == 201

    speaker_id = create_response.json()["id"]

    new_email = unique_email("updated")

    response = client.put(
        f"/api/v1/speakers/{speaker_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": new_email
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == new_email

