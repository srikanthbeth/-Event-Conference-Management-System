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
from utils.enums import VenueStatus, HallAvailabilityStatus

from models.venue import Venue
from models.hall import Hall

from models.attendee import Attendee
from models.checkin import CheckIn
from models.event import Event
from models.registration import Registration
from models.session import Session
from models.speaker import Speaker
from models.user import User

from utils.enums import (
    EventStatus,
    RegistrationStatus,
    UserRole,
)

from utils.security import hash_password


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="feedback"):
    return f"{prefix}_{uuid4().hex}@example.com"


def create_user(
    role: UserRole,
    prefix="feedback_user",
):
    db = SessionLocal()

    user = User(
        full_name=f"Test {prefix}",
        email=unique_email(prefix),
        phone="9876543210",
        hashed_password=hash_password("Password@123"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    user_id = user.id
    email = user.email

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
):
    db = SessionLocal()

    event = Event(
        event_name=f"Feedback Event {uuid4().hex[:8]}",
        description="Feedback test event",
        event_type="Conference",
        organizer_id=organizer_id,
        start_date=datetime.utcnow() + timedelta(days=2),
        end_date=datetime.utcnow() + timedelta(days=3),
        registration_start=datetime.utcnow() - timedelta(days=1),
        registration_end=datetime.utcnow() + timedelta(days=1),
        capacity=100,
        status=EventStatus.PUBLISHED,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    event_id = event.id

    db.close()

    return event_id


def create_speaker():
    db = SessionLocal()

    speaker = Speaker(
        name=f"Speaker {uuid4().hex[:8]}",
        email=unique_email("speaker"),
        phone="9876543211",
        bio="Test speaker",
        expertise="Technology",
        company="Test Company",
        experience=10,
    )

    db.add(speaker)
    db.commit()
    db.refresh(speaker)

    speaker_id = speaker.id

    db.close()

    return speaker_id


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

def create_registration(
    attendee_id,
    event_id,
    status=RegistrationStatus.CONFIRMED,
):
    db = SessionLocal()

    registration = Registration(
        attendee_id=attendee_id,
        event_id=event_id,
        registration_date=datetime.utcnow(),
        registration_status=status,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    registration_id = registration.id

    db.close()

    return registration_id


def create_checkin(registration_id):
    db = SessionLocal()

    checkin = CheckIn(
        registration_id=registration_id,
        check_in_time=datetime.utcnow(),
        check_in_method="Manual",
    )

    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    checkin_id = checkin.id

    db.close()

    return checkin_id


def create_hall():
    db = SessionLocal()

    venue = Venue(
        venue_name="Feedback Test Venue",
        address="123 Test Street",
        city="Hyderabad",
        capacity=500,
        facilities="Projector, WiFi, AC",
        status=VenueStatus.ACTIVE,
    )

    db.add(venue)
    db.commit()
    db.refresh(venue)

    hall = Hall(
        venue_id=venue.id,
        hall_name="Feedback Test Hall",
        capacity=100,
        floor=1,
        availability_status=HallAvailabilityStatus.AVAILABLE,
    )

    db.add(hall)
    db.commit()
    db.refresh(hall)

    hall_id = hall.id

    db.close()

    return hall_id

def create_session(event_id, speaker_id, hall_id):
    db = SessionLocal()

    now = datetime.utcnow()

    event_session = Session(
        event_id=event_id,
        speaker_id=speaker_id,
        hall_id=hall_id,
        title="Feedback Session",
        description="Session for feedback testing",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        capacity=50,
        session_type="Workshop",
    )

    db.add(event_session)
    db.commit()
    db.refresh(event_session)

    session_id = event_session.id

    db.close()

    return session_id

def setup_feedback_data():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer",
    )

    attendee_user_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee",
    )

    event_id = create_event(organizer_id)

    attendee_id = create_attendee(
        attendee_email
    )

    registration_id = create_registration(
        attendee_id,
        event_id,
    )

    create_checkin(
        registration_id
    )

    speaker_id = create_speaker()

    hall_id = create_hall()

    session_id = create_session(
        event_id,
        speaker_id,
        hall_id,
    )

    attendee_token = login(
        attendee_email
    )

    organizer_token = login(
        organizer_email
    )

    return {
        "event_id": event_id,
        "attendee_id": attendee_id,
        "registration_id": registration_id,
        "speaker_id": speaker_id,
        "session_id": session_id,
        "attendee_token": attendee_token,
        "organizer_token": organizer_token,
    }


def test_create_session_feedback():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "speaker_id": data["speaker_id"],
            "session_id": data["session_id"],
            "rating": 5,
            "feedback": "Excellent session",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["registration_id"] == data["registration_id"]
    assert body["event_id"] == data["event_id"]
    assert body["speaker_id"] == data["speaker_id"]
    assert body["session_id"] == data["session_id"]
    assert body["rating"] == 5
    assert body["feedback"] == "Excellent session"


def test_feedback_requires_authentication():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "rating": 5,
            "feedback": "Good",
        },
    )

    assert response.status_code == 401


def test_rating_cannot_be_zero():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "rating": 0,
            "feedback": "Bad",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 422


def test_rating_cannot_exceed_five():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "rating": 6,
            "feedback": "Excellent",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 422


def test_unchecked_attendee_cannot_submit_feedback():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_unchecked",
    )

    attendee_user_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_unchecked",
    )

    event_id = create_event(organizer_id)

    attendee_id = create_attendee(
        attendee_email
    )

    registration_id = create_registration(
        attendee_id,
        event_id,
    )

    token = login(attendee_email)

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": registration_id,
            "event_id": event_id,
            "rating": 4,
            "feedback": "Good event",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 400


def test_duplicate_session_feedback_prevented():
    data = setup_feedback_data()

    payload = {
        "registration_id": data["registration_id"],
        "event_id": data["event_id"],
        "speaker_id": data["speaker_id"],
        "session_id": data["session_id"],
        "rating": 5,
        "feedback": "Excellent",
    }

    first = client.post(
        "/api/v1/feedback",
        json=payload,
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/feedback",
        json=payload,
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert second.status_code == 400


def test_event_feedback_requires_valid_event():
    data = setup_feedback_data()

    response = client.get(
        "/api/v1/feedback/events/999999/feedback",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 404


def test_get_event_feedback():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "speaker_id": data["speaker_id"],
            "session_id": data["session_id"],
            "rating": 4,
            "feedback": "Very good",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/feedback/events/{data['event_id']}/feedback",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1
    assert body[0]["event_id"] == data["event_id"]


def test_get_speaker_ratings():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "speaker_id": data["speaker_id"],
            "session_id": data["session_id"],
            "rating": 5,
            "feedback": "Great speaker",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/feedback/speakers/{data['speaker_id']}/ratings",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1
    assert body[0]["speaker_id"] == data["speaker_id"]
    assert body[0]["rating"] == 5


def test_attendee_cannot_view_event_feedback():
    data = setup_feedback_data()

    response = client.get(
        f"/api/v1/feedback/events/{data['event_id']}/feedback",
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 403


def test_attendee_cannot_view_speaker_ratings():
    data = setup_feedback_data()

    response = client.get(
        f"/api/v1/feedback/speakers/{data['speaker_id']}/ratings",
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 403


def test_attendee_cannot_submit_feedback_for_another_registration():
    data = setup_feedback_data()

    other_user_id, other_email = create_user(
        UserRole.ATTENDEE,
        "other_attendee",
    )

    other_attendee_id = create_attendee(
        other_user_id
    )

    other_registration_id = create_registration(
        other_attendee_id,
        data["event_id"],
    )

    create_checkin(
        other_registration_id
    )

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": other_registration_id,
            "event_id": data["event_id"],
            "rating": 4,
            "feedback": "Good",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 403


def test_feedback_event_mismatch_rejected():
    data = setup_feedback_data()

    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "second_organizer",
    )

    another_event_id = create_event(
        organizer_id
    )

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": another_event_id,
            "rating": 4,
            "feedback": "Good",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 400


def test_session_from_another_event_rejected():
    data = setup_feedback_data()

    organizer_id, _ = create_user(
        UserRole.EVENT_ORGANIZER,
        "another_organizer",
    )

    another_event_id = create_event(
        organizer_id
    )

    another_speaker_id = create_speaker()

    another_hall_id = create_hall()
    
    another_session_id = create_session(
        another_event_id,
        another_speaker_id,
        another_hall_id,
    )

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "speaker_id": data["speaker_id"],
            "session_id": another_session_id,
            "rating": 4,
            "feedback": "Good",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 400


def test_speaker_not_found():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "speaker_id": 999999,
            "rating": 4,
            "feedback": "Good",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 404


def test_session_not_found():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "session_id": 999999,
            "rating": 4,
            "feedback": "Good",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 404


def test_attendee_cannot_create_feedback():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer_role",
    )

    attendee_user_id, attendee_email = create_user(
        UserRole.ATTENDEE,
        "attendee_role",
    )

    event_id = create_event(
        organizer_id
    )

    attendee_id = create_attendee(
        attendee_email
    )

    registration_id = create_registration(
        attendee_id,
        event_id,
    )

    create_checkin(
        registration_id
    )

    token = login(
        organizer_email
    )

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": registration_id,
            "event_id": event_id,
            "rating": 5,
            "feedback": "Good",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403

def test_event_feedback_without_speaker_or_session_allowed():
    data = setup_feedback_data()

    response = client.post(
        "/api/v1/feedback",
        json={
            "registration_id": data["registration_id"],
            "event_id": data["event_id"],
            "rating": 4,
            "feedback": "Good event",
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["registration_id"] == data["registration_id"]
    assert body["event_id"] == data["event_id"]
    assert body["speaker_id"] is None
    assert body["session_id"] is None
    assert body["rating"] == 4
    assert body["feedback"] == "Good event"