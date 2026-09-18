from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.attendee import Attendee
from models.checkin import CheckIn
from models.event import Event
from models.feedback import Feedback
from models.payment import Payment
from models.purchase import Purchase
from models.refund import Refund
from models.registration import Registration
from models.session import Session as EventSession
from models.session_booking import SessionBooking
from models.speaker import Speaker
from utils.enums import (
    EventStatus,
    PaymentStatus,
    SessionBookingStatus,
)


ACTIVE_EVENT_STATUSES = [
    EventStatus.PUBLISHED,
    EventStatus.REGISTRATION_OPEN,
    EventStatus.REGISTRATION_CLOSED,
]


class DashboardRepository:

    @staticmethod
    def get_admin_dashboard(db: Session) -> dict:
        total_events = (
            db.query(func.count(Event.id))
            .scalar()
            or 0
        )

        active_events = (
            db.query(func.count(Event.id))
            .filter(Event.status.in_(ACTIVE_EVENT_STATUSES))
            .scalar()
            or 0
        )

        completed_events = (
            db.query(func.count(Event.id))
            .filter(Event.status == EventStatus.COMPLETED)
            .scalar()
            or 0
        )

        total_attendees = (
            db.query(func.count(Attendee.id))
            .scalar()
            or 0
        )

        total_registrations = (
            db.query(func.count(Registration.id))
            .scalar()
            or 0
        )

        total_tickets_sold = (
            db.query(func.coalesce(func.sum(Purchase.quantity), 0))
            .join(
                Payment,
                Payment.purchase_id == Purchase.id,
            )
            .filter(
                Payment.payment_status == PaymentStatus.SUCCESSFUL
            )
            .scalar()
            or 0
        )

        total_revenue = (
            db.query(
                func.coalesce(
                    func.sum(Payment.amount),
                    Decimal("0.00"),
                )
            )
            .filter(
                Payment.payment_status == PaymentStatus.SUCCESSFUL
            )
            .scalar()
            or Decimal("0.00")
        )

        total_refunds = (
            db.query(
                func.coalesce(
                    func.sum(Refund.refund_amount),
                    Decimal("0.00"),
                )
            )
            .scalar()
            or Decimal("0.00")
        )

        average_event_rating = (
            db.query(func.avg(Feedback.rating))
            .scalar()
        )

        if average_event_rating is not None:
            average_event_rating = round(
                float(average_event_rating),
                2,
            )

        return {
            "total_events": total_events,
            "active_events": active_events,
            "completed_events": completed_events,
            "total_attendees": total_attendees,
            "total_registrations": total_registrations,
            "total_tickets_sold": int(total_tickets_sold),
            "total_revenue": Decimal(total_revenue),
            "total_refunds": Decimal(total_refunds),
            "average_event_rating": average_event_rating,
        }

    @staticmethod
    def get_organizer_dashboard(
        db: Session,
        organizer_id: int,
    ) -> dict:

        event_filter = Event.organizer_id == organizer_id

        event_registrations = (
            db.query(func.count(Registration.id))
            .join(
                Event,
                Registration.event_id == Event.id,
            )
            .filter(event_filter)
            .scalar()
            or 0
        )

        ticket_sales = (
            db.query(func.coalesce(func.sum(Purchase.quantity), 0))
            .join(
                Registration,
                Purchase.registration_id == Registration.id,
            )
            .join(
                Event,
                Registration.event_id == Event.id,
            )
            .join(
                Payment,
                Payment.purchase_id == Purchase.id,
            )
            .filter(
                event_filter,
                Payment.payment_status == PaymentStatus.SUCCESSFUL,
            )
            .scalar()
            or 0
        )

        revenue = (
            db.query(
                func.coalesce(
                    func.sum(Payment.amount),
                    Decimal("0.00"),
                )
            )
            .join(
                Purchase,
                Payment.purchase_id == Purchase.id,
            )
            .join(
                Registration,
                Purchase.registration_id == Registration.id,
            )
            .join(
                Event,
                Registration.event_id == Event.id,
            )
            .filter(
                event_filter,
                Payment.payment_status == PaymentStatus.SUCCESSFUL,
            )
            .scalar()
            or Decimal("0.00")
        )

        attendance = (
            db.query(
                func.count(func.distinct(CheckIn.registration_id))
            )
            .join(
                Registration,
                CheckIn.registration_id == Registration.id,
            )
            .join(
                Event,
                Registration.event_id == Event.id,
            )
            .filter(event_filter)
            .scalar()
            or 0
        )

        session_bookings = (
            db.query(func.count(SessionBooking.id))
            .join(
                EventSession,
                SessionBooking.session_id == EventSession.id,
            )
            .join(
                Event,
                EventSession.event_id == Event.id,
            )
            .filter(
                event_filter,
                SessionBooking.booking_status
                == SessionBookingStatus.BOOKED,
            )
            .scalar()
            or 0
        )

        speaker_performance = (
            db.query(
                Speaker.id.label("speaker_id"),
                Speaker.name.label("speaker_name"),
                func.avg(Feedback.rating).label("average_rating"),
                func.count(Feedback.id).label("feedback_count"),
            )
            .join(
                Feedback,
                Feedback.speaker_id == Speaker.id,
            )
            .join(
                Event,
                Feedback.event_id == Event.id,
            )
            .filter(event_filter)
            .group_by(
                Speaker.id,
                Speaker.name,
            )
            .order_by(Speaker.id)
            .all()
        )

        session_popularity = (
            db.query(
                EventSession.id.label("session_id"),
                EventSession.title.label("session_title"),
                func.count(SessionBooking.id).label(
                    "booking_count"
                ),
            )
            .join(
                SessionBooking,
                SessionBooking.session_id == EventSession.id,
            )
            .join(
                Event,
                EventSession.event_id == Event.id,
            )
            .filter(
                event_filter,
                SessionBooking.booking_status
                == SessionBookingStatus.BOOKED,
            )
            .group_by(
                EventSession.id,
                EventSession.title,
            )
            .order_by(EventSession.id)
            .all()
        )

        return {
            "event_registrations": event_registrations,
            "ticket_sales": int(ticket_sales),
            "revenue": Decimal(revenue),
            "attendance": attendance,
            "session_bookings": session_bookings,
            "speaker_performance": speaker_performance,
            "session_popularity": session_popularity,
        }