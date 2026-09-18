from database import SessionLocal
from services.notification_service import (
    NotificationService,
)


def send_registration_confirmation(
    user_id: int,
    event_name: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Registration Confirmation",
            title="Registration Confirmed",
            message=(
                f"Your registration for "
                f"'{event_name}' has been confirmed."
            ),
        )
    finally:
        db.close()


def send_payment_success(
    user_id: int,
    event_name: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Payment Success",
            title="Payment Successful",
            message=(
                f"Your payment for "
                f"'{event_name}' was successful."
            ),
        )
    finally:
        db.close()


def send_ticket_confirmation(
    user_id: int,
    event_name: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Ticket Confirmation",
            title="Ticket Confirmed",
            message=(
                f"Your ticket for "
                f"'{event_name}' has been confirmed."
            ),
        )
    finally:
        db.close()


def send_certificate_availability(
    user_id: int,
    event_name: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Certificate Availability",
            title="Certificate Available",
            message=(
                f"Your certificate for "
                f"'{event_name}' is now available."
            ),
        )
    finally:
        db.close()


def send_event_cancellation(
    user_id: int,
    event_name: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Event Cancellation",
            title="Event Cancelled",
            message=(
                f"The event '{event_name}' "
                "has been cancelled."
            ),
        )
    finally:
        db.close()


def send_event_reminder(
    user_id: int,
    event_name: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Event Reminder",
            title="Event Reminder",
            message=(
                f"Reminder: '{event_name}' "
                "is coming up."
            ),
        )
    finally:
        db.close()


def send_session_reminder(
    user_id: int,
    session_title: str,
):
    db = SessionLocal()

    try:
        NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type="Session Reminder",
            title="Session Reminder",
            message=(
                f"Reminder: your session "
                f"'{session_title}' is coming up."
            ),
        )
    finally:
        db.close()