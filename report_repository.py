from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.checkin import CheckIn
from models.event import Event
from models.feedback import Feedback
from models.payment import Payment
from models.purchase import Purchase
from models.registration import Registration
from models.session import Session as EventSession
from models.session_booking import SessionBooking
from models.speaker import Speaker
from models.ticket import Ticket
from utils.enums import PaymentStatus, SessionBookingStatus


class ReportRepository:

    @staticmethod
    def get_daily_registrations(
        db: Session,
        organizer_id: int | None = None,
    ):
        query = (
            db.query(
                func.date(
                    Registration.registration_date
                ).label("date"),
                func.count(Registration.id).label(
                    "registrations"
                ),
            )
            .join(
                Event,
                Registration.event_id == Event.id,
            )
        )

        if organizer_id is not None:
            query = query.filter(
                Event.organizer_id == organizer_id
            )

        return (
            query
            .group_by(
                func.date(Registration.registration_date)
            )
            .order_by(
                func.date(Registration.registration_date)
            )
            .all()
        )

    @staticmethod
    def get_event_revenue(
        db: Session,
        organizer_id: int | None = None,
    ):
        query = (
            db.query(
                Event.id.label("event_id"),
                Event.event_name.label("event_name"),
                func.coalesce(
                    func.sum(Payment.amount),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(
                Registration,
                Registration.event_id == Event.id,
            )
            .join(
                Purchase,
                Purchase.registration_id == Registration.id,
            )
            .join(
                Payment,
                Payment.purchase_id == Purchase.id,
            )
            .filter(
                Payment.payment_status
                == PaymentStatus.SUCCESSFUL
            )
        )

        if organizer_id is not None:
            query = query.filter(
                Event.organizer_id == organizer_id
            )

        return (
            query
            .group_by(
                Event.id,
                Event.event_name,
            )
            .order_by(Event.id)
            .all()
        )

    @staticmethod
    def get_ticket_sales(
        db: Session,
        organizer_id: int | None = None,
    ):
        query = (
            db.query(
                Event.id.label("event_id"),
                Event.event_name.label("event_name"),
                Ticket.id.label("ticket_id"),
                Ticket.ticket_type.label("ticket_type"),
                func.coalesce(
                    func.sum(Purchase.quantity),
                    0,
                ).label("tickets_sold"),
                func.coalesce(
                    func.sum(
                        Payment.amount
                    ),
                    Decimal("0.00"),
                ).label("revenue"),
            )
            .join(
                Purchase,
                Purchase.ticket_id == Ticket.id,
            )
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
                Payment.payment_status
                == PaymentStatus.SUCCESSFUL
            )
        )

        if organizer_id is not None:
            query = query.filter(
                Event.organizer_id == organizer_id
            )

        return (
            query
            .group_by(
                Event.id,
                Event.event_name,
                Ticket.id,
                Ticket.ticket_type,
            )
            .order_by(
                Event.id,
                Ticket.id,
            )
            .all()
        )

    @staticmethod
    def get_attendance(
        db: Session,
        organizer_id: int | None = None,
    ):
        registrations_query = (
            db.query(
                Event.id.label("event_id"),
                Event.event_name.label("event_name"),
                func.count(Registration.id).label(
                    "registrations"
                ),
            )
            .join(
                Registration,
                Registration.event_id == Event.id,
            )
        )

        if organizer_id is not None:
            registrations_query = registrations_query.filter(
                Event.organizer_id == organizer_id
            )

        registrations = (
            registrations_query
            .group_by(
                Event.id,
                Event.event_name,
            )
            .order_by(Event.id)
            .all()
        )

        attendance_query = (
            db.query(
                Event.id.label("event_id"),
                func.count(
                    func.distinct(CheckIn.registration_id)
                ).label("attendance"),
            )
            .join(
                Registration,
                Registration.event_id == Event.id,
            )
            .join(
                CheckIn,
                CheckIn.registration_id == Registration.id,
            )
        )

        if organizer_id is not None:
            attendance_query = attendance_query.filter(
                Event.organizer_id == organizer_id
            )

        attendance = (
            attendance_query
            .group_by(Event.id)
            .all()
        )

        attendance_map = {
            row.event_id: row.attendance
            for row in attendance
        }

        return [
            {
                "event_id": row.event_id,
                "event_name": row.event_name,
                "registrations": row.registrations,
                "attendance": attendance_map.get(
                    row.event_id,
                    0,
                ),
            }
            for row in registrations
        ]

    @staticmethod
    def get_speaker_ratings(
        db: Session,
        organizer_id: int | None = None,
    ):
        query = (
            db.query(
                Speaker.id.label("speaker_id"),
                Speaker.name.label("speaker_name"),
                func.avg(
                    Feedback.rating
                ).label("average_rating"),
                func.count(
                    Feedback.id
                ).label("rating_count"),
            )
            .join(
                Feedback,
                Feedback.speaker_id == Speaker.id,
            )
            .join(
                Event,
                Feedback.event_id == Event.id,
            )
        )

        if organizer_id is not None:
            query = query.filter(
                Event.organizer_id == organizer_id
            )

        return (
            query
            .group_by(
                Speaker.id,
                Speaker.name,
            )
            .order_by(Speaker.id)
            .all()
        )

    @staticmethod
    def get_session_popularity(
        db: Session,
        organizer_id: int | None = None,
    ):
        query = (
            db.query(
                EventSession.id.label("session_id"),
                EventSession.title.label(
                    "session_title"
                ),
                Event.id.label("event_id"),
                Event.event_name.label("event_name"),
                func.count(
                    SessionBooking.id
                ).label("booking_count"),
            )
            .join(
                SessionBooking,
                SessionBooking.session_id
                == EventSession.id,
            )
            .join(
                Event,
                EventSession.event_id == Event.id,
            )
            .filter(
                SessionBooking.booking_status
                == SessionBookingStatus.BOOKED
            )
        )

        if organizer_id is not None:
            query = query.filter(
                Event.organizer_id == organizer_id
            )

        return (
            query
            .group_by(
                EventSession.id,
                EventSession.title,
                Event.id,
                Event.event_name,
            )
            .order_by(EventSession.id)
            .all()
        )