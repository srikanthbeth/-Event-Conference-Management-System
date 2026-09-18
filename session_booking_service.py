from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.attendee import Attendee
from models.session import Session as EventSession
from models.session_booking import SessionBooking
from models.user import User

from repositories.session_booking_repository import (
    SessionBookingRepository,
)

from utils.enums import (
    RegistrationStatus,
    SessionBookingStatus,
    UserRole,
)


class SessionBookingService:

    @staticmethod
    def _get_attendee_for_user(
        db: Session,
        current_user: User,
    ) -> Attendee:

        attendee = (
            db.query(Attendee)
            .filter(
                Attendee.email == current_user.email,
            )
            .first()
        )

        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendee profile not found",
            )

        return attendee

    @staticmethod
    def book_session(
        db: Session,
        session_id: int,
        current_user: User,
    ):

        if current_user.role != UserRole.ATTENDEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only attendees can book sessions",
            )

        attendee = (
            SessionBookingService
            ._get_attendee_for_user(
                db,
                current_user,
            )
        )

        event_session = (
            db.query(EventSession)
            .filter(
                EventSession.id == session_id,
            )
            .first()
        )

        if not event_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        registration = None

        for item in attendee.registrations:
            if item.event_id == event_session.event_id:
                registration = item
                break

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not registered for this event",
            )

        if (
            registration.registration_status
            != RegistrationStatus.CONFIRMED
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only confirmed attendees can book sessions",
            )

        existing_booking = (
            SessionBookingRepository
            .get_by_attendee_and_session(
                db,
                attendee.id,
                session_id,
            )
        )

        if existing_booking:
            if (
                existing_booking.booking_status
                == SessionBookingStatus.BOOKED
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session already booked",
                )

        booked_count = (
            SessionBookingRepository
            .count_booked_for_session(
                db,
                session_id,
            )
        )

        if booked_count >= event_session.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session capacity has been reached",
            )

        if existing_booking:
            existing_booking.booking_status = (
                SessionBookingStatus.BOOKED
            )

            db.commit()
            db.refresh(existing_booking)

            return existing_booking

        booking = SessionBooking(
            attendee_id=attendee.id,
            session_id=session_id,
            booking_status=SessionBookingStatus.BOOKED,
        )

        return SessionBookingRepository.create(
            db,
            booking,
        )

    @staticmethod
    def get_attendee_sessions(
        db: Session,
        attendee_id: int,
        current_user: User,
    ):

        # First verify that the requested attendee exists.
        # This ensures a nonexistent attendee returns 404
        # before ownership/permission checks are performed.
        attendee = (
            db.query(Attendee)
            .filter(
                Attendee.id == attendee_id,
            )
            .first()
        )

        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendee not found",
            )

        # Admin can view any attendee's sessions.
        if current_user.role != UserRole.ADMIN:

            current_attendee = (
                db.query(Attendee)
                .filter(
                    Attendee.email == current_user.email,
                )
                .first()
            )

            if not current_attendee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendee profile not found",
                )

            if current_attendee.id != attendee_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot access another attendee's sessions",
                )

        return SessionBookingRepository.get_by_attendee(
            db,
            attendee_id,
        )

    @staticmethod
    def cancel_booking(
        db: Session,
        booking_id: int,
        current_user: User,
    ):

        booking = (
            SessionBookingRepository.get_by_id(
                db,
                booking_id,
            )
        )

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session booking not found",
            )

        if current_user.role != UserRole.ADMIN:

            attendee = (
                db.query(Attendee)
                .filter(
                    Attendee.email == current_user.email,
                )
                .first()
            )

            if not attendee:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Attendee profile not found",
                )

            if booking.attendee_id != attendee.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot cancel this booking",
                )

        SessionBookingRepository.delete(
            db,
            booking,
        )

        return {
            "message": "Session booking cancelled successfully"
        }