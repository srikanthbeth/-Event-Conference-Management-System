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


def unique_email(prefix="venue"):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_user(role="Event Organizer"):
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


def venue_payload():
    return {
        "venue_name": "Hyderabad Convention Center",
        "address": "Hitech City Road",
        "city": "Hyderabad",
        "capacity": 2000,
        "facilities": "Parking, WiFi, AC, Projector",
        "status": "Active",
    }


def hall_payload():
    return {
        "hall_name": "Main Hall",
        "capacity": 1000,
        "floor": 1,
        "availability_status": "Available",
    }


def test_create_venue():
    email = register_user()
    token = login_user(email)

    response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=venue_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["venue_name"] == (
        "Hyderabad Convention Center"
    )
    assert data["address"] == "Hitech City Road"
    assert data["city"] == "Hyderabad"
    assert data["capacity"] == 2000
    assert data["status"] == "Active"


def test_create_venue_requires_authentication():
    response = client.post(
        "/api/v1/venues",
        json=venue_payload(),
    )

    assert response.status_code == 401


def test_attendee_cannot_create_venue():
    email = register_user("Attendee")
    token = login_user(email)

    response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=venue_payload(),
    )

    assert response.status_code == 403


def test_get_venues():
    email = register_user()
    token = login_user(email)

    client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=venue_payload(),
    )

    response = client.get(
        "/api/v1/venues"
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_create_hall_under_venue():
    email = register_user()
    token = login_user(email)

    venue_response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=venue_payload(),
    )

    assert venue_response.status_code == 201

    venue_id = venue_response.json()["id"]

    response = client.post(
        f"/api/v1/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=hall_payload(),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["venue_id"] == venue_id
    assert data["hall_name"] == "Main Hall"
    assert data["capacity"] == 1000
    assert data["floor"] == 1


def test_create_hall_requires_authentication():
    email = register_user()
    token = login_user(email)

    venue_response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=venue_payload(),
    )

    venue_id = venue_response.json()["id"]

    response = client.post(
        f"/api/v1/venues/{venue_id}/halls",
        json=hall_payload(),
    )

    assert response.status_code == 401


def test_hall_capacity_cannot_exceed_venue_capacity():
    email = register_user()
    token = login_user(email)

    payload = venue_payload()
    payload["capacity"] = 500

    venue_response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    venue_id = venue_response.json()["id"]

    hall = hall_payload()
    hall["capacity"] = 501

    response = client.post(
        f"/api/v1/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=hall,
    )

    assert response.status_code == 400


def test_hall_venue_must_exist():
    email = register_user()
    token = login_user(email)

    response = client.post(
        "/api/v1/venues/999999/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=hall_payload(),
    )

    assert response.status_code == 404


def test_get_halls_for_venue():
    email = register_user()
    token = login_user(email)

    venue_response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=venue_payload(),
    )

    venue_id = venue_response.json()["id"]

    client.post(
        f"/api/v1/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=hall_payload(),
    )

    response = client.get(
        f"/api/v1/venues/{venue_id}/halls"
    )

    assert response.status_code == 200

    halls = response.json()

    assert len(halls) == 1
    assert halls[0]["venue_id"] == venue_id
    assert halls[0]["hall_name"] == "Main Hall"


def test_get_halls_for_nonexistent_venue():
    response = client.get(
        "/api/v1/venues/999999/halls"
    )

    assert response.status_code == 404


def test_attendee_cannot_create_hall():
    organizer_email = register_user()
    organizer_token = login_user(organizer_email)

    venue_response = client.post(
        "/api/v1/venues",
        headers={
            "Authorization": f"Bearer {organizer_token}"
        },
        json=venue_payload(),
    )

    venue_id = venue_response.json()["id"]

    attendee_email = register_user("Attendee")
    attendee_token = login_user(attendee_email)

    response = client.post(
        f"/api/v1/venues/{venue_id}/halls",
        headers={
            "Authorization": f"Bearer {attendee_token}"
        },
        json=hall_payload(),
    )

    assert response.status_code == 403