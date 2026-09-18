import os
from datetime import datetime, timedelta
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


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_organizer():
    email = register_user("Event Organizer")
    token = login_user(email)

    return email, token


def create_event(
    token,
    start_date=None,
    end_date=None,
):
    start_date = start_date or (
        datetime.now() + timedelta(days=10)
    )

    end_date = end_date or (
        start_date + timedelta(hours=8)
    )

    payload = {
        "event_name": "Technology Conference",
        "description": "Annual technology conference",
        "event_type": "Conference",
        "organizer_id": None,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "registration_start": (
            start_date - timedelta(days=5)
        ).isoformat(),
        "registration_end": (
            start_date - timedelta(hours=1)
        ).isoformat(),
        "capacity": 500,
        "status": "Draft",
    }

    response = client.post(
        "/api/v1/events",
        headers=auth_headers(token),
        json=payload,
    )

    if response.status_code == 422:
        payload.pop("organizer_id", None)

        response = client.post(
            "/api/v1/events",
            headers=auth_headers(token),
            json=payload,
        )

    assert response.status_code == 201

    return response.json()


def create_venue(token):
    payload = {
        "venue_name": f"Convention Center {uuid4().hex[:6]}",
        "address": "123 Main Street",
        "city": "Hyderabad",
        "capacity": 1000,
        "facilities": "Parking, WiFi, AC",
        "status": "Active",
    }

    response = client.post(
        "/api/v1/venues",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_hall(token, venue_id, capacity=500):
    payload = {
        "hall_name": f"Hall {uuid4().hex[:6]}",
        "capacity": capacity,
        "floor": 1,
        "availability_status": "Available",
    }

    response = client.post(
        f"/api/v1/venues/{venue_id}/halls",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def create_speaker(token, email=None):
    payload = {
        "name": "John Smith",
        "email": email or unique_email("speaker"),
        "phone": "9876543210",
        "bio": "Technology conference speaker",
        "expertise": "Artificial Intelligence",
        "company": "Tech Solutions",
        "experience": 10,
    }

    response = client.post(
        "/api/v1/speakers",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201

    return response.json()


def session_payload(
    event_id,
    speaker_id,
    hall_id,
    start_time,
    end_time,
    capacity=200,
):
    return {
        "event_id": event_id,
        "speaker_id": speaker_id,
        "hall_id": hall_id,
        "title": "Introduction to Artificial Intelligence",
        "description": "AI session for conference attendees",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "capacity": capacity,
        "session_type": "Technical",
    }


def create_test_setup():
    email, token = create_organizer()

    event_start = datetime.now() + timedelta(days=10)
    event_end = event_start + timedelta(hours=8)

    event = create_event(
        token,
        start_date=event_start,
        end_date=event_end,
    )

    venue = create_venue(token)

    hall = create_hall(
        token,
        venue["id"],
        capacity=500,
    )

    speaker = create_speaker(token)

    session_start = event_start + timedelta(hours=1)
    session_end = event_start + timedelta(hours=2)

    return {
        "email": email,
        "token": token,
        "event": event,
        "venue": venue,
        "hall": hall,
        "speaker": speaker,
        "session_start": session_start,
        "session_end": session_end,
    }


def test_create_session():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["event_id"] == setup["event"]["id"]
    assert data["speaker_id"] == setup["speaker"]["id"]
    assert data["hall_id"] == setup["hall"]["id"]
    assert data["title"] == "Introduction to Artificial Intelligence"
    assert data["capacity"] == 200
    assert data["session_type"] == "Technical"


def test_create_session_requires_authentication():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    response = client.post(
        "/api/v1/sessions",
        json=payload,
    )

    assert response.status_code == 401


def test_attendee_cannot_create_session():
    organizer_email = register_user("Event Organizer")
    organizer_token = login_user(organizer_email)

    event_start = datetime.now() + timedelta(days=10)
    event_end = event_start + timedelta(hours=8)

    event = create_event(
        organizer_token,
        event_start,
        event_end,
    )

    venue = create_venue(organizer_token)

    hall = create_hall(
        organizer_token,
        venue["id"],
    )

    speaker = create_speaker(
        organizer_token,
    )

    attendee_email = register_user("Attendee")
    attendee_token = login_user(attendee_email)

    payload = session_payload(
        event["id"],
        speaker["id"],
        hall["id"],
        event_start + timedelta(hours=1),
        event_start + timedelta(hours=2),
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(attendee_token),
        json=payload,
    )

    assert response.status_code == 403


def test_get_sessions():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    create_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/v1/sessions"
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_session():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    create_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/sessions/{session_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == session_id
    assert data["event_id"] == setup["event"]["id"]


def test_session_not_found():
    response = client.get(
        "/api/v1/sessions/999999"
    )

    assert response.status_code == 404


def test_update_session():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    create_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers(setup["token"]),
        json={
            "title": "Updated AI Session",
            "description": "Updated session description",
            "capacity": 250,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == session_id
    assert data["title"] == "Updated AI Session"
    assert data["description"] == "Updated session description"
    assert data["capacity"] == 250


def test_update_session_requires_authentication():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    create_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sessions/{session_id}",
        json={
            "title": "Unauthorized Update"
        },
    )

    assert response.status_code == 401


def test_attendee_cannot_update_session():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    create_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    attendee_email = register_user("Attendee")
    attendee_token = login_user(attendee_email)

    response = client.put(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers(attendee_token),
        json={
            "title": "Unauthorized Update"
        },
    )

    assert response.status_code == 403


def test_delete_session():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    create_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers(setup["token"]),
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/api/v1/sessions/{session_id}"
    )

    assert get_response.status_code == 404


def test_session_end_time_must_be_after_start_time():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_start"],
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert response.status_code == 422


def test_session_cannot_start_before_event():
    setup = create_test_setup()

    start_time = (
        datetime.fromisoformat(
            setup["event"]["start_date"]
        )
        - timedelta(hours=1)
        if isinstance(
            setup["event"]["start_date"],
            str,
        )
        else setup["session_start"]
        - timedelta(days=1)
    )

    end_time = start_time + timedelta(hours=1)

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        start_time,
        end_time,
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert response.status_code == 400


def test_session_cannot_end_after_event():
    setup = create_test_setup()

    event_end = (
        datetime.fromisoformat(
            setup["event"]["end_date"]
        )
        if isinstance(
            setup["event"]["end_date"],
            str,
        )
        else setup["session_end"]
        + timedelta(days=1)
    )

    start_time = event_end - timedelta(hours=1)
    end_time = event_end + timedelta(hours=1)

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        start_time,
        end_time,
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert response.status_code == 400


def test_session_capacity_cannot_exceed_hall_capacity():
    setup = create_test_setup()

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
        capacity=1000,
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert response.status_code == 400
    assert "hall capacity" in response.json()["detail"].lower()


def test_inactive_speaker_cannot_be_assigned():
    setup = create_test_setup()

    deactivate_response = client.put(
        f"/api/v1/speakers/{setup['speaker']['id']}",
        headers=auth_headers(setup["token"]),
        json={
            "is_active": False
        },
    )

    assert deactivate_response.status_code == 200

    payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=payload,
    )

    assert response.status_code == 400
    assert "inactive speaker" in response.json()["detail"].lower()


def test_speaker_cannot_have_overlapping_sessions():
    setup = create_test_setup()

    first_payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    first_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_start = setup["session_start"] + timedelta(
        minutes=30
    )

    second_end = setup["session_end"] + timedelta(
        minutes=30
    )

    second_payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        second_start,
        second_end,
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=second_payload,
    )

    assert response.status_code == 400
    assert "speaker" in response.json()["detail"].lower()
    assert "overlapping" in response.json()["detail"].lower()


def test_hall_cannot_have_overlapping_sessions():
    setup = create_test_setup()

    first_payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    first_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_speaker = create_speaker(
        setup["token"]
    )

    second_start = setup["session_start"] + timedelta(
        minutes=30
    )

    second_end = setup["session_end"] + timedelta(
        minutes=30
    )

    second_payload = session_payload(
        setup["event"]["id"],
        second_speaker["id"],
        setup["hall"]["id"],
        second_start,
        second_end,
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=second_payload,
    )

    assert response.status_code == 400
    assert "hall" in response.json()["detail"].lower()
    assert "overlapping" in response.json()["detail"].lower()


def test_non_overlapping_sessions_are_allowed():
    setup = create_test_setup()

    first_payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    first_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_speaker = create_speaker(
        setup["token"]
    )

    second_start = setup["session_end"]
    second_end = second_start + timedelta(
        hours=1
    )

    second_payload = session_payload(
        setup["event"]["id"],
        second_speaker["id"],
        setup["hall"]["id"],
        second_start,
        second_end,
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=second_payload,
    )

    assert response.status_code == 201


def test_update_session_cannot_create_speaker_overlap():
    setup = create_test_setup()

    first_payload = session_payload(
        setup["event"]["id"],
        setup["speaker"]["id"],
        setup["hall"]["id"],
        setup["session_start"],
        setup["session_end"],
    )

    first_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=first_payload,
    )

    assert first_response.status_code == 201

    second_speaker = create_speaker(
        setup["token"]
    )

    second_start = setup["session_end"] + timedelta(
        hours=1
    )

    second_end = second_start + timedelta(
        hours=1
    )

    second_payload = session_payload(
        setup["event"]["id"],
        second_speaker["id"],
        setup["hall"]["id"],
        second_start,
        second_end,
    )

    second_response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(setup["token"]),
        json=second_payload,
    )

    assert second_response.status_code == 201

    second_session_id = second_response.json()["id"]

    response = client.put(
        f"/api/v1/sessions/{second_session_id}",
        headers=auth_headers(setup["token"]),
        json={
            "speaker_id": setup["speaker"]["id"],
            "start_time": setup["session_start"].isoformat(),
            "end_time": setup["session_end"].isoformat(),
        },
    )

    assert response.status_code == 400
    assert "speaker" in response.json()["detail"].lower()


def test_admin_can_create_session():
    email = register_user("Admin")
    token = login_user(email)

    event_start = datetime.now() + timedelta(days=10)
    event_end = event_start + timedelta(hours=8)

    event = create_event(
        token,
        event_start,
        event_end,
    )

    venue = create_venue(token)

    hall = create_hall(
        token,
        venue["id"],
    )

    speaker = create_speaker(token)

    payload = session_payload(
        event["id"],
        speaker["id"],
        hall["id"],
        event_start + timedelta(hours=1),
        event_start + timedelta(hours=2),
    )

    response = client.post(
        "/api/v1/sessions",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201