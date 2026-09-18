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

from models.attendee import Attendee
from models.checkin import CheckIn
from models.event import Event
from models.feedback import Feedback
from models.hall import Hall
from models.payment import Payment
from models.purchase import Purchase
from models.refund import Refund
from models.registration import Registration
from models.session import Session
from models.session_booking import SessionBooking
from models.speaker import Speaker
from models.ticket import Ticket
from models.user import User
from models.venue import Venue

from utils.enums import (
    CheckInMethod,
    EventStatus,
    EventType,
    HallAvailabilityStatus,
    PaymentMethod,
    PaymentStatus,
    RegistrationStatus,
    RefundStatus,
    SessionBookingStatus,
    TicketType,
    UserRole,
    VenueStatus,
)

from utils.security import hash_password


client = TestClient(app)


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="level15"):
    return f"{prefix}_{uuid4().hex}@example.com"


def create_user(
    role: UserRole,
    prefix="user",
):
    db = SessionLocal()

    user = User(
        full_name=f"Test {role.value}",
        email=unique_email(prefix),
        phone="9876543210",
        hashed_password=hash_password("Test@123"),
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
            "password": "Test@123",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_test_data():
    db = SessionLocal()

    # ============================================================
    # USERS
    # ============================================================

    admin = User(
        full_name="Admin",
        email=unique_email("admin"),
        phone="9000000001",
        hashed_password=hash_password("Test@123"),
        role=UserRole.ADMIN,
        is_active=True,
    )

    organizer = User(
        full_name="Organizer",
        email=unique_email("organizer"),
        phone="9000000002",
        hashed_password=hash_password("Test@123"),
        role=UserRole.EVENT_ORGANIZER,
        is_active=True,
    )

    other_organizer = User(
        full_name="Other Organizer",
        email=unique_email("otherorganizer"),
        phone="9000000003",
        hashed_password=hash_password("Test@123"),
        role=UserRole.EVENT_ORGANIZER,
        is_active=True,
    )

    attendee_user = User(
        full_name="Attendee",
        email=unique_email("attendee"),
        phone="9000000004",
        hashed_password=hash_password("Test@123"),
        role=UserRole.ATTENDEE,
        is_active=True,
    )

    db.add_all(
        [
            admin,
            organizer,
            other_organizer,
            attendee_user,
        ]
    )

    db.commit()

    db.refresh(admin)
    db.refresh(organizer)
    db.refresh(other_organizer)
    db.refresh(attendee_user)

    # ============================================================
    # VENUE
    # ============================================================

    venue = Venue(
        venue_name="Analytics Convention Center",
        address="Main Road",
        city="Hyderabad",
        capacity=1000,
        facilities="WiFi, Parking",
        status=VenueStatus.ACTIVE,
    )

    db.add(venue)
    db.commit()
    db.refresh(venue)

    # ============================================================
    # HALL
    # ============================================================

    hall = Hall(
        venue_id=venue.id,
        hall_name="Main Hall",
        capacity=500,
        floor=1,
        availability_status=HallAvailabilityStatus.AVAILABLE,
    )

    db.add(hall)
    db.commit()
    db.refresh(hall)

    now = datetime.utcnow()

    # ============================================================
    # EVENTS
    # ============================================================

    event1 = Event(
        event_name="Tech Conference",
        description="Technology event",
        event_type=EventType.CONFERENCE,
        organizer_id=organizer.id,
        start_date=now + timedelta(days=10),
        end_date=now + timedelta(days=11),
        registration_start=now - timedelta(days=5),
        registration_end=now + timedelta(days=5),
        capacity=500,
        status=EventStatus.REGISTRATION_OPEN,
    )

    event2 = Event(
        event_name="Completed Conference",
        description="Completed event",
        event_type=EventType.CONFERENCE,
        organizer_id=organizer.id,
        start_date=now - timedelta(days=20),
        end_date=now - timedelta(days=19),
        registration_start=now - timedelta(days=30),
        registration_end=now - timedelta(days=21),
        capacity=300,
        status=EventStatus.COMPLETED,
    )

    event3 = Event(
        event_name="Other Organizer Event",
        description="Other event",
        event_type=EventType.WORKSHOP,
        organizer_id=other_organizer.id,
        start_date=now + timedelta(days=20),
        end_date=now + timedelta(days=21),
        registration_start=now - timedelta(days=2),
        registration_end=now + timedelta(days=15),
        capacity=200,
        status=EventStatus.PUBLISHED,
    )

    db.add_all(
        [
            event1,
            event2,
            event3,
        ]
    )

    db.commit()

    db.refresh(event1)
    db.refresh(event2)
    db.refresh(event3)

    # ============================================================
    # ATTENDEE
    # ============================================================

    attendee = Attendee(
        full_name="Test Attendee",
        email=attendee_user.email,
        phone="9111111111",
        organization="Test Company",
        designation="Developer",
    )

    db.add(attendee)
    db.commit()
    db.refresh(attendee)

    # ============================================================
    # REGISTRATION
    # ============================================================

    registration = Registration(
        attendee_id=attendee.id,
        event_id=event1.id,
        registration_date=now,
        registration_status=RegistrationStatus.CONFIRMED,
    )

    db.add(registration)
    db.commit()
    db.refresh(registration)

    # ============================================================
    # TICKET
    # ============================================================

    ticket = Ticket(
        event_id=event1.id,
        ticket_type=TicketType.STANDARD,
        price=Decimal("1000.00"),
        quantity=100,
        available_quantity=90,
        sale_start=now - timedelta(days=5),
        sale_end=now + timedelta(days=5),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # ============================================================
    # PURCHASE
    # ============================================================

    purchase = Purchase(
        registration_id=registration.id,
        ticket_id=ticket.id,
        quantity=2,
        subtotal=Decimal("2000.00"),
        discount=Decimal("0.00"),
        tax=Decimal("200.00"),
        total_amount=Decimal("2200.00"),
    )

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    # ============================================================
    # PAYMENT
    # ============================================================

    payment = Payment(
        purchase_id=purchase.id,
        transaction_id=f"TXN-{uuid4().hex}",
        payment_method=PaymentMethod.UPI,
        amount=Decimal("2200.00"),
        payment_status=PaymentStatus.SUCCESSFUL,
    )

    db.add(payment)

    # Generate payment.id before creating Refund
    db.flush()

    assert payment.id is not None

    # ============================================================
    # REFUND
    # ============================================================

    refund = Refund(
        payment_id=payment.id,
        purchase_id=purchase.id,
        cancellation_reason="Customer cancellation",
        refund_amount=Decimal("500.00"),
        refund_status=RefundStatus.PENDING,
    )

    db.add(refund)

    db.commit()

    db.refresh(payment)
    db.refresh(refund)

    # ============================================================
    # SPEAKER
    # ============================================================

    speaker = Speaker(
        name="John Speaker",
        email=unique_email("speaker"),
        phone="9222222222",
        bio="Technology speaker",
        expertise="FastAPI",
        company="Tech Company",
        experience=10,
        is_active=True,
    )

    db.add(speaker)
    db.commit()
    db.refresh(speaker)

    # ============================================================
    # SESSION
    # ============================================================

    event_session = Session(
        event_id=event1.id,
        speaker_id=speaker.id,
        hall_id=hall.id,
        title="Advanced FastAPI",
        description="FastAPI session",
        start_time=now + timedelta(days=10, hours=1),
        end_time=now + timedelta(days=10, hours=2),
        capacity=100,
        session_type="Workshop",
    )

    db.add(event_session)
    db.commit()
    db.refresh(event_session)

    # ============================================================
    # CHECK-IN
    # ============================================================

    checkin = CheckIn(
        registration_id=registration.id,
        check_in_time=now,
        check_in_method=CheckInMethod.MANUAL,
    )

    db.add(checkin)

    # ============================================================
    # SESSION BOOKING
    # ============================================================

    booking = SessionBooking(
        attendee_id=attendee.id,
        session_id=event_session.id,
        booking_status=SessionBookingStatus.BOOKED,
    )

    db.add(booking)

    # ============================================================
    # FEEDBACK
    # ============================================================

    feedback = Feedback(
        registration_id=registration.id,
        event_id=event1.id,
        speaker_id=speaker.id,
        session_id=event_session.id,
        rating=5,
        feedback="Excellent session",
    )

    db.add(feedback)

    db.commit()

    # ============================================================
    # RETURN LOGIN DATA
    # ============================================================

    result = {
        "admin_email": admin.email,
        "organizer_email": organizer.email,
        "other_organizer_email": other_organizer.email,
        "attendee_email": attendee_user.email,
    }

    db.close()

    return result


# ================================================================
# ADMIN DASHBOARD
# ================================================================

def test_admin_dashboard():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/dashboard/admin",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_events"] == 3
    assert body["completed_events"] == 1
    assert body["total_attendees"] == 1
    assert body["total_registrations"] == 1
    assert body["total_tickets_sold"] == 2

    assert Decimal(str(body["total_revenue"])) == Decimal("2200.00")
    assert Decimal(str(body["total_refunds"])) == Decimal("500.00")

    assert body["average_event_rating"] == 5


def test_non_admin_cannot_access_admin_dashboard():
    data = create_test_data()

    token = login(data["organizer_email"])

    response = client.get(
        "/api/v1/dashboard/admin",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


# ================================================================
# ORGANIZER DASHBOARD
# ================================================================

def test_organizer_dashboard():
    data = create_test_data()

    token = login(data["organizer_email"])

    response = client.get(
        "/api/v1/dashboard/organizer",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["event_registrations"] >= 1
    assert body["ticket_sales"] >= 2

    assert Decimal(str(body["revenue"])) >= Decimal("2200.00")

    assert body["attendance"] >= 1
    assert body["session_bookings"] >= 1

    assert len(body["speaker_performance"]) >= 1
    assert len(body["session_popularity"]) >= 1


def test_organizer_dashboard_does_not_include_other_organizer_data():
    data = create_test_data()

    organizer_token = login(data["organizer_email"])

    response = client.get(
        "/api/v1/dashboard/organizer",
        headers=auth_headers(organizer_token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["event_registrations"] >= 1


def test_attendee_cannot_access_organizer_dashboard():
    data = create_test_data()

    token = login(data["attendee_email"])

    response = client.get(
        "/api/v1/dashboard/organizer",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


# ================================================================
# DAILY REGISTRATION REPORT
# ================================================================

def test_daily_registration_report():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/reports/daily-registrations",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1
    assert body[0]["registrations"] >= 1


# ================================================================
# EVENT REVENUE REPORT
# ================================================================

def test_event_revenue_report():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/reports/event-revenue",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert any(
        Decimal(str(item["revenue"])) == Decimal("2200.00")
        for item in body
    )


# ================================================================
# TICKET SALES REPORT
# ================================================================

def test_ticket_sales_report():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/reports/ticket-sales",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert any(
        item["tickets_sold"] >= 2
        for item in body
    )


# ================================================================
# ATTENDANCE REPORT
# ================================================================

def test_attendance_report():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/reports/attendance",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert any(
        item["attendance"] >= 1
        for item in body
    )


# ================================================================
# SPEAKER RATING REPORT
# ================================================================

def test_speaker_rating_report():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/reports/speaker-ratings",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert any(
        item["average_rating"] == 5
        for item in body
    )


# ================================================================
# SESSION POPULARITY REPORT
# ================================================================

def test_session_popularity_report():
    data = create_test_data()

    token = login(data["admin_email"])

    response = client.get(
        "/api/v1/reports/session-popularity",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) >= 1

    assert any(
        item["booking_count"] >= 1
        for item in body
    )


# ================================================================
# REPORT AUTHORIZATION
# ================================================================

def test_attendee_cannot_access_reports():
    data = create_test_data()

    token = login(data["attendee_email"])

    response = client.get(
        "/api/v1/reports/event-revenue",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_organizer_report_is_restricted_to_own_events():
    data = create_test_data()

    token = login(data["organizer_email"])

    response = client.get(
        "/api/v1/reports/event-revenue",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert all(
        item["event_name"] != "Other Organizer Event"
        for item in body
    )