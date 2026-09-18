from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.event import Event
from models.registration import Registration
from models.user import User
from repositories.attendee_repository import AttendeeRepository
from repositories.registration_repository import RegistrationRepository
from services.attendee_service import AttendeeService
from utils.enums import (
    EventStatus,
    RegistrationStatus,
    UserRole,
)


class RegistrationService:

    @staticmethod
    def _check_attendee(
        current_user: User,
    ) -> None:

        if current_user.role != UserRole.ATTENDEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only attendees can register for events",
            )

        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive users cannot register for events",
            )

    @staticmethod
    def register(
        db: Session,
        event_id: int,
        current_user: User,
    ):

        RegistrationService._check_attendee(
            current_user
        )

        event = db.get(
            Event,
            event_id,
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        if event.status == EventStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancelled event cannot accept registrations",
            )

        now = datetime.utcnow()

        if (
            now < event.registration_start
            or now > event.registration_end
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration is not currently open",
            )

        attendee = AttendeeService.get_or_create_from_user(
            db,
            current_user,
        )

        existing = (
            RegistrationRepository
            .get_by_attendee_and_event(
                db,
                attendee.id,
                event_id,
            )
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already registered for this event",
            )

        active_count = (
            RegistrationRepository
            .count_active_for_event(
                db,
                event_id,
            )
        )

        if active_count >= event.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event capacity reached",
            )

        registration = Registration(
            attendee_id=attendee.id,
            event_id=event_id,
            registration_date=now,
            registration_status=(
                RegistrationStatus.PENDING
            ),
        )

        return RegistrationRepository.create(
            db,
            registration,
        )

    @staticmethod
    def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        event_id: int | None = None,
        registration_status=None,
        registration_date: datetime | None = None,
        sort_by: str = "registration_date",
        sort_order: str = "desc",
    ):
        return RegistrationRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            event_id=event_id,
            registration_status=registration_status,
            registration_date=registration_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    def get_by_id(
        db: Session,
        registration_id: int,
    ):

        registration = (
            RegistrationRepository.get_by_id(
                db,
                registration_id,
            )
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )

        return registration

    @staticmethod
    def cancel(
        db: Session,
        registration_id: int,
        current_user: User,
    ):

        RegistrationService._check_attendee(
            current_user
        )

        registration = RegistrationService.get_by_id(
            db,
            registration_id,
        )

        attendee = AttendeeRepository.get_by_id(
            db,
            registration.attendee_id,
        )

        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendee not found",
            )

        if attendee.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own registration",
            )

        if (
            registration.registration_status
            == RegistrationStatus.CANCELLED
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration is already cancelled",
            )

        registration.registration_status = (
            RegistrationStatus.CANCELLED
        )

        return RegistrationRepository.update(
            db,
            registration,
            {
                "registration_status": (
                    RegistrationStatus.CANCELLED
                )
            },
        )