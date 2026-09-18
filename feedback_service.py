from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.attendee import Attendee
from models.checkin import CheckIn
from models.event import Event
from models.feedback import Feedback
from models.registration import Registration
from models.session import Session as EventSession
from models.speaker import Speaker
from models.user import User
from repositories.feedback_repository import FeedbackRepository
from schemas.feedback import FeedbackCreate
from utils.enums import RegistrationStatus, UserRole


class FeedbackService:

    @staticmethod
    def _get_attendee_for_user(
        db: Session,
        user: User,
    ) -> Attendee:
        """
        Find the attendee profile using the logged-in
        user's email.

        The existing Attendee model does not contain user_id,
        so email is used to associate the authenticated user
        with the attendee.
        """

        attendee = (
            db.query(Attendee)
            .filter(
                Attendee.email == user.email
            )
            .first()
        )

        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Attendee profile not found",
            )

        return attendee

    @staticmethod
    def create_feedback(
        db: Session,
        payload: FeedbackCreate,
        current_user: User,
    ) -> Feedback:

        # Only attendees can submit feedback
        if current_user.role != UserRole.ATTENDEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only attendees can provide feedback",
            )

        attendee = FeedbackService._get_attendee_for_user(
            db,
            current_user,
        )

        # Find registration
        registration = (
            db.query(Registration)
            .filter(
                Registration.id == payload.registration_id
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )

        # Registration must belong to logged-in attendee
        if registration.attendee_id != attendee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You can only provide feedback "
                    "for your own registration"
                ),
            )

        # Registration must belong to requested event
        if registration.event_id != payload.event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration does not belong to this event",
            )

        # Registration must be confirmed or attended
        if registration.registration_status not in (
            RegistrationStatus.CONFIRMED,
            RegistrationStatus.ATTENDED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Only confirmed or attended registrations "
                    "can provide feedback"
                ),
            )

        # IMPORTANT:
        # The assignment requires the attendee to have checked in.
        check_in = (
            db.query(CheckIn)
            .filter(
                CheckIn.registration_id
                == registration.id
            )
            .first()
        )

        if not check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Attendee must check in "
                    "before providing feedback"
                ),
            )

        # Check event
        event = (
            db.query(Event)
            .filter(
                Event.id == payload.event_id
            )
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        # Check speaker if supplied
        if payload.speaker_id is not None:

            speaker = (
                db.query(Speaker)
                .filter(
                    Speaker.id == payload.speaker_id
                )
                .first()
            )

            if not speaker:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Speaker not found",
                )

        # Check session if supplied
        if payload.session_id is not None:

            event_session = (
                db.query(EventSession)
                .filter(
                    EventSession.id
                    == payload.session_id
                )
                .first()
            )

            if not event_session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found",
                )

            # Session must belong to same event
            if event_session.event_id != payload.event_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Session does not belong to this event",
                )

            # Prevent duplicate feedback for same session
            existing_feedback = (
                FeedbackRepository.get_by_registration_and_session(
                    db,
                    registration.id,
                    payload.session_id,
                )
            )

            if existing_feedback:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Feedback already submitted "
                        "for this session"
                    ),
                )

        feedback = Feedback(
            registration_id=payload.registration_id,
            event_id=payload.event_id,
            speaker_id=payload.speaker_id,
            session_id=payload.session_id,
            rating=payload.rating,
            feedback=payload.feedback,
        )

        return FeedbackRepository.create(
            db,
            feedback,
        )

    @staticmethod
    def get_event_feedback(
        db: Session,
        event_id: int,
        current_user: User,
    ) -> list[Feedback]:

        event = (
            db.query(Event)
            .filter(
                Event.id == event_id
            )
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        allowed_roles = {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        }

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to view event feedback"
                ),
            )

        return FeedbackRepository.get_by_event(
            db,
            event_id,
        )

    @staticmethod
    def get_speaker_ratings(
        db: Session,
        speaker_id: int,
        current_user: User,
    ) -> list[Feedback]:

        speaker = (
            db.query(Speaker)
            .filter(
                Speaker.id == speaker_id
            )
            .first()
        )

        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker not found",
            )

        allowed_roles = {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        }

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to view speaker ratings"
                ),
            )

        return FeedbackRepository.get_by_speaker(
            db,
            speaker_id,
        )