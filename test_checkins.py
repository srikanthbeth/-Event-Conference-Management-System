
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
from models.hall import Hall
from models.registration import Registration
from models.session import Session as EventSession
from models.speaker import Speaker
from models.user import User
from models.venue import Venue

from utils.enums import (
    CheckInMethod,
    EventStatus,
    EventType,
    HallAvailabilityStatus,
    RegistrationStatus,
    UserRole,
)

from utils.security import hash_password


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def unique_email(prefix="checkin"):
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

    assert response.status_code == 201, response.text

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


def create_user_directly(
    role=UserRole.ATTENDEE,
    prefix="direct",
):
    email = unique_email(prefix)

    db = SessionLocal()

    try:
        user = User(
            full_name=f"Direct {prefix}",
            email=email,
            phone="9876543210",
            password_hash=hash_password("Test@12345"),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user
    finally:
        db.close()


def create_admin():
    email = register_user(
        UserRole.ADMIN,
        "admin",
    )

    return {
        "email": email,
        "token": login_user(email),
    }


def create_organizer():
    email = register_user(
        UserRole.EVENT_ORGANIZER,
        "organizer",
    )

    return {
        "email": email,
        "token": login_user(email),
    }


def create_staff():
    email = register_user(
        UserRole.STAFF,
        "staff",
    )

    return {
        "email": email,
        "token": login_user(email),
    }


def create_attendee():
    email = register_user(
        UserRole.ATTENDEE,
        "attendee",
    )

    return {
        "email": email,
        "token": login_user(email),
    }


def create_speaker():
    db = SessionLocal()

    try:
        speaker = Speaker(
            name=f"Speaker {uuid4().hex[:8]}",
            email=unique_email("speaker"),
            phone="9876543210",
            bio="Test speaker",
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


def create_venue_and_hall(
    capacity=100,
):
    db = SessionLocal()

    try:
        venue = Venue(
            venue_name=f"Venue {uuid4().hex[:8]}",
            address="Test Address",
            city="Hyderabad",
            capacity=capacity,
            facilities="Projector, WiFi",
        )

        db.add(venue)
        db.commit()
        db.refresh(venue)

        hall = Hall(
            venue_id=venue.id,
            hall_name=f"Hall {uuid4().hex[:8]}",
            capacity=capacity,
            floor=1,
            availability_status=HallAvailabilityStatus.AVAILABLE,
        )

        db.add(hall)
        db.commit()
        db.refresh(hall)

        return venue.id, hall.id

    finally:
        db.close()


def create_event(
    organizer_email,
    status=EventStatus.REGISTRATION_OPEN,
):
    db = SessionLocal()

    try:
        organizer = (
            db.query(User)
            .filter(
                User.email == organizer_email,
            )
            .first()
        )

        assert organizer is not None

        start_date = datetime.utcnow() + timedelta(days=2)
        end_date = start_date + timedelta(hours=8)

        event = Event(
            event_name=f"Event {uuid4().hex[:8]}",
            description="Test event",
            event_type=EventType.CONFERENCE,
            organizer_id=organizer.id,
            start_date=start_date,
            end_date=end_date,
            registration_start=datetime.utcnow() - timedelta(days=1),
            registration_end=start_date - timedelta(hours=1),
            capacity=100,
            status=status,
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        return event.id

    finally:
        db.close()


def create_attendee_profile(
    attendee_email,
):
    db = SessionLocal()

    try:
        attendee = Attendee(
            full_name="Test Attendee",
            email=attendee_email,
            phone="9876543210",
            organization="Test Organization",
            designation="Developer",
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
    status=RegistrationStatus.CONFIRMED,
):
    db = SessionLocal()

    try:
        registration = Registration(
            attendee_id=attendee_id,
            event_id=event_id,
            registration_status=status,
        )

        db.add(registration)
        db.commit()
        db.refresh(registration)

        return registration.id

    finally:
        db.close()


def create_complete_attendance_data(
    registration_status=RegistrationStatus.CONFIRMED,
):
    organizer = create_organizer()
    attendee = create_attendee()

    event_id = create_event(
        organizer["email"],
    )

    attendee_id = create_attendee_profile(
        attendee["email"],
    )

    registration_id = create_registration(
        attendee_id,
        event_id,
        registration_status,
    )

    return {
        "organizer": organizer,
        "attendee": attendee,
        "event_id": event_id,
        "attendee_id": attendee_id,
        "registration_id": registration_id,
    }


# -------------------------------------------------------------------
# Check-In Tests
# -------------------------------------------------------------------

def test_confirmed_registration_can_check_in():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["registration_id"] == data["registration_id"]
    assert body["check_in_method"] == CheckInMethod.MANUAL.value
    assert body["check_in_time"] is not None
    assert body["check_out_time"] is None


def test_check_in_requires_authentication():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
    )

    assert response.status_code == 401


def test_attendee_cannot_check_in():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["attendee"]["token"],
        ),
    )

    assert response.status_code == 403


def test_speaker_cannot_check_in():
    data = create_complete_attendance_data()

    speaker_email = register_user(
        UserRole.SPEAKER,
        "speaker_user",
    )

    speaker_token = login_user(
        speaker_email,
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(speaker_token),
    )

    assert response.status_code == 403


def test_registration_not_found_for_check_in():
    organizer = create_organizer()

    response = client.post(
        "/api/v1/registrations/999999/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            organizer["token"],
        ),
    )

    assert response.status_code == 404


def test_pending_registration_cannot_check_in():
    data = create_complete_attendance_data(
        RegistrationStatus.PENDING,
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 403


def test_cancelled_registration_cannot_check_in():
    data = create_complete_attendance_data(
        RegistrationStatus.CANCELLED,
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 403


def test_duplicate_check_in_is_prevented():
    data = create_complete_attendance_data()

    first_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert second_response.status_code == 400


# -------------------------------------------------------------------
# Check-In Method Tests
# -------------------------------------------------------------------

def test_qr_code_check_in_method():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.QR_CODE.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 201
    assert (
        response.json()["check_in_method"]
        == CheckInMethod.QR_CODE.value
    )


def test_manual_check_in_method():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 201
    assert (
        response.json()["check_in_method"]
        == CheckInMethod.MANUAL.value
    )


def test_staff_check_in_method():
    data = create_complete_attendance_data()
    staff = create_staff()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.STAFF.value,
        },
        headers=auth_headers(
            staff["token"],
        ),
    )

    assert response.status_code == 201
    assert (
        response.json()["check_in_method"]
        == CheckInMethod.STAFF.value
    )


def test_invalid_check_in_method_is_rejected():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": "Invalid",
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 422


def test_missing_check_in_method_is_rejected():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 422


# -------------------------------------------------------------------
# Check-Out Tests
# -------------------------------------------------------------------

def test_check_out_after_check_in():
    data = create_complete_attendance_data()

    check_in_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert check_in_response.status_code == 201

    check_out_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert check_out_response.status_code == 200

    body = check_out_response.json()

    assert body["registration_id"] == data["registration_id"]
    assert body["check_in_time"] is not None
    assert body["check_out_time"] is not None


def test_check_out_requires_authentication():
    data = create_complete_attendance_data()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
    )

    assert response.status_code == 401


def test_attendee_cannot_check_out():
    data = create_complete_attendance_data()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["attendee"]["token"],
        ),
    )

    assert response.status_code == 403


def test_check_out_without_check_in_is_rejected():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 400


def test_duplicate_check_out_is_prevented():
    data = create_complete_attendance_data()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    first_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert second_response.status_code == 400


def test_registration_not_found_for_check_out():
    organizer = create_organizer()

    response = client.post(
        "/api/v1/registrations/999999/check-out",
        headers=auth_headers(
            organizer["token"],
        ),
    )

    assert response.status_code == 404


# -------------------------------------------------------------------
# Role Authorization Tests
# -------------------------------------------------------------------

def test_admin_can_check_in():
    data = create_complete_attendance_data()
    admin = create_admin()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            admin["token"],
        ),
    )

    assert response.status_code == 201


def test_event_organizer_can_check_in():
    data = create_complete_attendance_data()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 201


def test_staff_can_check_in():
    data = create_complete_attendance_data()
    staff = create_staff()

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.STAFF.value,
        },
        headers=auth_headers(
            staff["token"],
        ),
    )

    assert response.status_code == 201


def test_admin_can_check_out():
    data = create_complete_attendance_data()
    admin = create_admin()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            admin["token"],
        ),
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            admin["token"],
        ),
    )

    assert response.status_code == 200


def test_staff_can_check_out():
    data = create_complete_attendance_data()
    staff = create_staff()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.STAFF.value,
        },
        headers=auth_headers(
            staff["token"],
        ),
    )

    response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            staff["token"],
        ),
    )

    assert response.status_code == 200


# -------------------------------------------------------------------
# Attendance History Tests
# -------------------------------------------------------------------

def test_event_attendance_history():
    data = create_complete_attendance_data()

    check_in_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert check_in_response.status_code == 201

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["registration_id"] == data["registration_id"]


def test_event_attendance_history_after_check_out():
    data = create_complete_attendance_data()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.QR_CODE.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["check_in_time"] is not None
    assert body[0]["check_out_time"] is not None
    assert (
        body[0]["check_in_method"]
        == CheckInMethod.QR_CODE.value
    )


def test_event_attendance_history_returns_empty_list():
    data = create_complete_attendance_data()

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_attendance_history_requires_authentication():
    data = create_complete_attendance_data()

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
    )

    assert response.status_code == 401


def test_attendee_cannot_view_attendance_history():
    data = create_complete_attendance_data()

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            data["attendee"]["token"],
        ),
    )

    assert response.status_code == 403


def test_speaker_cannot_view_attendance_history():
    data = create_complete_attendance_data()

    speaker_email = register_user(
        UserRole.SPEAKER,
        "history_speaker",
    )

    speaker_token = login_user(
        speaker_email,
    )

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(speaker_token),
    )

    assert response.status_code == 403


def test_admin_can_view_attendance_history():
    data = create_complete_attendance_data()
    admin = create_admin()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            admin["token"],
        ),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_staff_can_view_attendance_history():
    data = create_complete_attendance_data()
    staff = create_staff()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.STAFF.value,
        },
        headers=auth_headers(
            staff["token"],
        ),
    )

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            staff["token"],
        ),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_event_organizer_can_view_attendance_history():
    data = create_complete_attendance_data()

    client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.MANUAL.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_attendance_history_maintains_complete_record():
    data = create_complete_attendance_data()

    check_in_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-in",
        params={
            "check_in_method": CheckInMethod.QR_CODE.value,
        },
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert check_in_response.status_code == 201

    check_in_body = check_in_response.json()

    check_out_response = client.post(
        f"/api/v1/registrations/{data['registration_id']}/check-out",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert check_out_response.status_code == 200

    check_out_body = check_out_response.json()

    response = client.get(
        f"/api/v1/events/{data['event_id']}/attendance",
        headers=auth_headers(
            data["organizer"]["token"],
        ),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1

    record = body[0]

    assert record["id"] == check_in_body["id"]
    assert (
        record["registration_id"]
        == data["registration_id"]
    )
    assert (
        record["check_in_time"]
        == check_in_body["check_in_time"]
    )
    assert (
        record["check_out_time"]
        == check_out_body["check_out_time"]
    )
    assert (
        record["check_in_method"]
        == CheckInMethod.QR_CODE.value
    )

