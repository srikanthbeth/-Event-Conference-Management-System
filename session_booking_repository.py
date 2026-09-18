from sqlalchemy.orm import Session

from models.session_booking import SessionBooking
from utils.enums import SessionBookingStatus


class SessionBookingRepository:

    @staticmethod
    def create(
        db: Session,
        booking: SessionBooking,
    ) -> SessionBooking:

        db.add(booking)
        db.commit()
        db.refresh(booking)

        return booking

    @staticmethod
    def get_by_id(
        db: Session,
        booking_id: int,
    ) -> SessionBooking | None:

        return (
            db.query(SessionBooking)
            .filter(SessionBooking.id == booking_id)
            .first()
        )

    @staticmethod
    def get_by_attendee_and_session(
        db: Session,
        attendee_id: int,
        session_id: int,
    ) -> SessionBooking | None:

        return (
            db.query(SessionBooking)
            .filter(
                SessionBooking.attendee_id == attendee_id,
                SessionBooking.session_id == session_id,
            )
            .first()
        )

    @staticmethod
    def get_by_attendee(
        db: Session,
        attendee_id: int,
    ) -> list[SessionBooking]:

        return (
            db.query(SessionBooking)
            .filter(
                SessionBooking.attendee_id == attendee_id,
                SessionBooking.booking_status
                == SessionBookingStatus.BOOKED,
            )
            .order_by(SessionBooking.id)
            .all()
        )

    @staticmethod
    def count_booked_for_session(
        db: Session,
        session_id: int,
    ) -> int:

        return (
            db.query(SessionBooking)
            .filter(
                SessionBooking.session_id == session_id,
                SessionBooking.booking_status
                == SessionBookingStatus.BOOKED,
            )
            .count()
        )

    @staticmethod
    def delete(
        db: Session,
        booking: SessionBooking,
    ) -> None:

        db.delete(booking)
        db.commit()