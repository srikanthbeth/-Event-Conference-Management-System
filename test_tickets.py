
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
from models.user import User
from utils.enums import UserRole


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="ticket"):
    return f"{prefix}_{uuid4().hex}@example.com"


def register_user(
    role=UserRole.EVENT_ORGANIZER,
    prefix="ticket_user",
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


def get_user_email(user_id):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        assert user is not None

        return user.email

    finally:
        db.close()


def create_organizer_and_login():
    email = register_user(
        role=UserRole.EVENT_ORGANIZER,
        prefix="organizer",
    )

    token = login_user(email)

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        assert user is not None

        return user.id, token

    finally:
        db.close()


def create_event(token, event_name=None):
    if event_name is None:
        event_name = f"Event {uuid4().hex[:8]}"

    now = datetime.utcnow()

    payload = {
        "event_name": event_name,
        "description": "Ticket management test event",
        "event_type": "Conference",
        "start_date": (now + timedelta(days=10)).isoformat(),
        "end_date": (now + timedelta(days=11)).isoformat(),
        "registration_start": (now - timedelta(days=1)).isoformat(),
        "registration_end": (now + timedelta(days=9)).isoformat(),
        "capacity": 500,
        "status": "Published",
    }

    response = client.post(
        "/api/v1/events",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def ticket_payload(
    ticket_type="Standard",
    price="999.00",
    quantity=100,
    available_quantity=100,
    sale_start=None,
    sale_end=None,
):
    now = datetime.utcnow()

    if sale_start is None:
        sale_start = now - timedelta(hours=1)

    if sale_end is None:
        sale_end = now + timedelta(days=5)

    return {
        "ticket_type": ticket_type,
        "price": price,
        "quantity": quantity,
        "available_quantity": available_quantity,
        "sale_start": sale_start.isoformat(),
        "sale_end": sale_end.isoformat(),
    }


def test_create_standard_ticket():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Standard",
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["event_id"] == event_id
    assert data["ticket_type"] == "Standard"
    assert Decimal(str(data["price"])) == Decimal("999.00")
    assert data["quantity"] == 100
    assert data["available_quantity"] == 100


def test_create_vip_ticket():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="VIP",
            price="2500.00",
            quantity=50,
            available_quantity=50,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["ticket_type"] == "VIP"


def test_create_early_bird_ticket():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Early Bird",
            price="699.00",
            quantity=75,
            available_quantity=75,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["ticket_type"] == "Early Bird"


def test_create_student_ticket():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Student",
            price="499.00",
            quantity=100,
            available_quantity=100,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["ticket_type"] == "Student"


def test_create_ticket_requires_authentication():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(),
    )

    assert response.status_code == 401


def test_non_organizer_cannot_create_ticket():
    organizer_id, _ = create_organizer_and_login()

    attendee_email = register_user(
        role=UserRole.ATTENDEE,
        prefix="attendee",
    )

    attendee_token = login_user(attendee_email)

    organizer_email = get_user_email(organizer_id)

    event_token = login_user(organizer_email)
    event_id = create_event(event_token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(),
        headers={
            "Authorization": f"Bearer {attendee_token}",
        },
    )

    assert response.status_code == 403


def test_event_not_found():
    _, token = create_organizer_and_login()

    response = client.post(
        "/api/v1/events/999999/tickets",
        json=ticket_payload(),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


def test_negative_price_rejected():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            price="-100.00",
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


def test_negative_quantity_rejected():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            quantity=-10,
            available_quantity=0,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


def test_negative_available_quantity_rejected():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            quantity=100,
            available_quantity=-1,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422


def test_available_quantity_cannot_exceed_quantity():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            quantity=100,
            available_quantity=120,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400


def test_sale_end_must_be_after_sale_start():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    now = datetime.utcnow()

    response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            sale_start=now + timedelta(days=5),
            sale_end=now + timedelta(days=2),
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400


def test_duplicate_ticket_category_rejected():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    first_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Standard",
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Standard",
            price="1200.00",
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert second_response.status_code == 400


def test_list_event_tickets():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    standard_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Standard",
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert standard_response.status_code == 201

    vip_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="VIP",
            price="2500.00",
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert vip_response.status_code == 201

    response = client.get(
        f"/api/v1/events/{event_id}/tickets",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["event_id"] == event_id
    assert data[1]["event_id"] == event_id


def test_list_tickets_event_not_found():
    response = client.get(
        "/api/v1/events/999999/tickets",
    )

    assert response.status_code == 404


def test_update_ticket():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    create_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Standard",
            price="999.00",
            quantity=100,
            available_quantity=100,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tickets/{ticket_id}",
        json={
            "price": "1299.00",
            "quantity": 120,
            "available_quantity": 110,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert Decimal(str(data["price"])) == Decimal("1299.00")
    assert data["quantity"] == 120
    assert data["available_quantity"] == 110


def test_update_ticket_requires_authentication():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    create_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tickets/{ticket_id}",
        json={
            "price": "1500.00",
        },
    )

    assert response.status_code == 401


def test_update_ticket_not_found():
    _, token = create_organizer_and_login()

    response = client.put(
        "/api/v1/tickets/999999",
        json={
            "price": "1500.00",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


def test_update_ticket_invalid_available_quantity():
    _, token = create_organizer_and_login()
    event_id = create_event(token)

    create_response = client.post(
        f"/api/v1/events/{event_id}/tickets",
        json=ticket_payload(
            ticket_type="Standard",
            quantity=100,
            available_quantity=100,
        ),
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert create_response.status_code == 201

    ticket_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/tickets/{ticket_id}",
        json={
            "available_quantity": 150,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400

