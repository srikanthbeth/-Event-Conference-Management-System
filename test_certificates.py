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
from models.checkin import CheckIn
from models.event import Event
from models.registration import Registration
from models.speaker import Speaker
from models.user import User
from models.venue import Venue
from models.hall import Hall

from utils.enums import (
    CertificateStatus,
    CertificateType,
    CheckInMethod,
    EventStatus,
    EventType,
    RegistrationStatus,
    UserRole,
    VenueStatus,
    HallAvailabilityStatus,
)

from utils.security import hash_password


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="certificate"):
    return f"{prefix}_{uuid4().hex}@example.com"


def create_user(
    role: UserRole,
    prefix="certificate_user",
):
    db = SessionLocal()

    user = User(
        full_name=f"Certificate {role.value} User",
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



def login_user(email):
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


def create_attendee_user():
    user_id, email = create_user(
        UserRole.ATTENDEE,
        "attendee",
    )

    db = SessionLocal()

    attendee = Attendee(
        id=user_id,
        full_name="Test Attendee",
        email=email,
        phone="9876543210",
        organization="Test Organization",
        designation="Developer",
    )

    db.add(attendee)
    db.commit()
    db.refresh(attendee)

    attendee_id = attendee.id

    db.close()

    return user_id, email, attendee_id


def create_event(organizer_id):
    db = SessionLocal()

    event = Event(
        event_name=f"Certificate Event {uuid4().hex[:8]}",
        description="Certificate testing event",
        event_type=EventType.CONFERENCE,
        organizer_id=organizer_id,
        start_date=datetime.utcnow() + timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=2),
        registration_start=datetime.utcnow() - timedelta(days=1),
        registration_end=datetime.utcnow() + timedelta(hours=12),
        capacity=100,
        status=EventStatus.PUBLISHED,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    event_id = event.id

    db.close()

    return event_id


def create_confirmed_registration(
    attendee_id,
    event_id,
):
    db = SessionLocal()

    registration = Registration(
        attendee_id=attendee_id,
        event_id=event_id,
        registration_date=datetime.utcnow(),
        registration_status=RegistrationStatus.CONFIRMED,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    registration_id = registration.id

    db.close()

    return registration_id


def create_checkin(registration_id):
    db = SessionLocal()

    check_in = CheckIn(
        registration_id=registration_id,
        check_in_time=datetime.utcnow(),
        check_in_method=CheckInMethod.MANUAL,
    )

    db.add(check_in)
    db.commit()

    db.close()


def setup_certificate_data():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "organizer",
    )

    organizer_token = login_user(
        organizer_email
    )

    attendee_user_id, attendee_email, attendee_id = (
        create_attendee_user()
    )

    attendee_token = login_user(
        attendee_email
    )

    event_id = create_event(
        organizer_id
    )

    registration_id = create_confirmed_registration(
        attendee_id,
        event_id,
    )

    create_checkin(
        registration_id
    )

    return {
        "organizer_id": organizer_id,
        "organizer_token": organizer_token,
        "attendee_user_id": attendee_user_id,
        "attendee_token": attendee_token,
        "attendee_id": attendee_id,
        "event_id": event_id,
        "registration_id": registration_id,
    }


def test_generate_certificate_success():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["registration_id"] == data["registration_id"]
    assert body["event_id"] == data["event_id"]
    assert body["attendee_id"] == data["attendee_id"]
    assert body["certificate_type"] == "Participation"
    assert body["status"] == "Issued"
    assert body["certificate_number"].startswith(
        "CERT-"
    )


def test_generate_certificate_requires_authentication():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
    )

    assert response.status_code == 401


def test_generate_certificate_registration_not_found():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "missing_registration_organizer",
    )

    token = login_user(organizer_email)

    response = client.post(
        "/api/v1/registrations/999999/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_unchecked_in_attendee_cannot_receive_certificate():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "unchecked_organizer",
    )

    token = login_user(organizer_email)

    _, _, attendee_id = create_attendee_user()

    event_id = create_event(organizer_id)

    registration_id = create_confirmed_registration(
        attendee_id,
        event_id,
    )

    response = client.post(
        f"/api/v1/registrations/"
        f"{registration_id}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_pending_registration_cannot_receive_certificate():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "pending_organizer",
    )

    token = login_user(organizer_email)

    _, _, attendee_id = create_attendee_user()

    event_id = create_event(organizer_id)

    db = SessionLocal()

    registration = Registration(
        attendee_id=attendee_id,
        event_id=event_id,
        registration_date=datetime.utcnow(),
        registration_status=RegistrationStatus.PENDING,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    registration_id = registration.id

    db.close()

    create_checkin(registration_id)

    response = client.post(
        f"/api/v1/registrations/"
        f"{registration_id}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_cancelled_registration_cannot_receive_certificate():
    organizer_id, organizer_email = create_user(
        UserRole.EVENT_ORGANIZER,
        "cancelled_organizer",
    )

    token = login_user(organizer_email)

    _, _, attendee_id = create_attendee_user()

    event_id = create_event(organizer_id)

    db = SessionLocal()

    registration = Registration(
        attendee_id=attendee_id,
        event_id=event_id,
        registration_date=datetime.utcnow(),
        registration_status=RegistrationStatus.CANCELLED,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    registration_id = registration.id

    db.close()

    create_checkin(registration_id)

    response = client.post(
        f"/api/v1/registrations/"
        f"{registration_id}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_duplicate_certificate_prevented():
    data = setup_certificate_data()

    first = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Completion"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert second.status_code == 400


def test_certificate_number_is_generated():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Completion"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201

    certificate_number = response.json()[
        "certificate_number"
    ]

    assert certificate_number.startswith("CERT-")
    assert len(certificate_number) >= 16


def test_participation_certificate():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201
    assert response.json()["certificate_type"] == "Participation"


def test_completion_certificate():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Completion"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201
    assert response.json()["certificate_type"] == "Completion"


def test_speaker_certificate():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Speaker"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201
    assert response.json()["certificate_type"] == "Speaker"


def test_invalid_certificate_type():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Invalid Type"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 422


def test_get_certificate_success():
    data = setup_certificate_data()

    create_response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    certificate_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/certificates/{certificate_id}",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == certificate_id


def test_get_certificate_not_found():
    data = setup_certificate_data()

    response = client.get(
        "/api/v1/certificates/999999",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 404


def test_get_certificate_requires_authentication():
    data = setup_certificate_data()

    create_response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    certificate_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/certificates/{certificate_id}"
    )

    assert response.status_code == 401


def test_attendee_can_view_own_certificate():
    data = setup_certificate_data()

    create_response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    certificate_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/certificates/{certificate_id}",
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 200


def test_attendee_cannot_view_another_certificate():
    data = setup_certificate_data()

    create_response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    certificate_id = create_response.json()["id"]

    _, other_email, _ = create_attendee_user()

    other_token = login_user(
        other_email
    )

    response = client.get(
        f"/api/v1/certificates/{certificate_id}",
        headers=auth_headers(
            other_token
        ),
    )

    assert response.status_code == 403


def test_get_attendee_certificates():
    data = setup_certificate_data()

    client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    response = client.get(
        f"/api/v1/attendees/"
        f"{data['attendee_id']}/certificates",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_attendee_can_view_own_certificate_list():
    data = setup_certificate_data()

    client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    response = client.get(
        f"/api/v1/attendees/"
        f"{data['attendee_id']}/certificates",
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_attendee_cannot_view_another_attendee_certificates():
    data = setup_certificate_data()

    _, other_email, other_attendee_id = create_attendee_user()

    response = client.get(
        f"/api/v1/attendees/"
        f"{other_attendee_id}/certificates",
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 403


def test_attendee_certificates_empty():
    data = setup_certificate_data()

    response = client.get(
        f"/api/v1/attendees/"
        f"{data['attendee_id']}/certificates",
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_attendee_not_found():
    data = setup_certificate_data()

    response = client.get(
        "/api/v1/attendees/999999/certificates",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 404


def test_get_event_certificates():
    data = setup_certificate_data()

    client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    response = client.get(
        f"/api/v1/events/"
        f"{data['event_id']}/certificates",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_event_certificates_empty():
    data = setup_certificate_data()

    response = client.get(
        f"/api/v1/events/"
        f"{data['event_id']}/certificates",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200
    assert response.json() == []


def test_event_not_found():
    data = setup_certificate_data()

    response = client.get(
        "/api/v1/events/999999/certificates",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 404


def test_attendee_cannot_generate_certificate():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["attendee_token"]
        ),
    )

    assert response.status_code == 403


def test_speaker_cannot_generate_certificate():
    data = setup_certificate_data()

    _, speaker_email = create_user(
        UserRole.SPEAKER,
        "speaker",
    )

    speaker_token = login_user(
        speaker_email
    )

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            speaker_token
        ),
    )

    assert response.status_code == 403


def test_admin_can_generate_certificate():
    data = setup_certificate_data()

    _, admin_email = create_user(
        UserRole.ADMIN,
        "admin",
    )

    admin_token = login_user(
        admin_email
    )

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            admin_token
        ),
    )

    assert response.status_code == 201


def test_staff_can_generate_certificate():
    data = setup_certificate_data()

    _, staff_email = create_user(
        UserRole.STAFF,
        "staff",
    )

    staff_token = login_user(
        staff_email
    )

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Completion"
        },
        headers=auth_headers(
            staff_token
        ),
    )

    assert response.status_code == 201


def test_organizer_can_view_event_certificates():
    data = setup_certificate_data()

    client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    response = client.get(
        f"/api/v1/events/"
        f"{data['event_id']}/certificates",
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 200


def test_certificate_status_is_issued():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "Issued"


def test_certificate_issue_date_is_generated():
    data = setup_certificate_data()

    before = datetime.utcnow()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Participation"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    after = datetime.utcnow()

    assert response.status_code == 201

    issue_date = datetime.fromisoformat(
        response.json()["issue_date"].replace(
            "Z",
            "+00:00",
        )
    )

    issue_date = issue_date.replace(
        tzinfo=None
    )

    assert before <= issue_date <= after


def test_certificate_contains_complete_details():
    data = setup_certificate_data()

    response = client.post(
        f"/api/v1/registrations/"
        f"{data['registration_id']}/certificate",
        json={
            "certificate_type": "Completion"
        },
        headers=auth_headers(
            data["organizer_token"]
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["certificate_number"]
    assert body["registration_id"] == data["registration_id"]
    assert body["event_id"] == data["event_id"]
    assert body["attendee_id"] == data["attendee_id"]
    assert body["issue_date"]
    assert body["certificate_type"] == "Completion"
    assert body["status"] == "Issued"