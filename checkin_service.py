from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.attendee import Attendee
from models.checkin import CheckIn
from models.registration import Registration
from models.user import User

from repositories.checkin_repository import (
    CheckInRepository,
)

from utils.enums import (
    CheckInMethod,
    RegistrationStatus,
    UserRole,
)


class CheckInService:

    @staticmethod
    def _validate_staff_role(
        current_user: User,
    ):
        allowed_roles = {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        }

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage attendance",
            )

    @staticmethod
    def check_in(
        db: Session,
        registration_id: int,
        check_in_method: CheckInMethod,
        current_user: User,
    ):

        # Only Admin, Event Organizer, and Staff
        # can check in attendees.
        CheckInService._validate_staff_role(
            current_user,
        )

        registration = (
            db.query(Registration)
            .filter(
                Registration.id == registration_id,
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )

        # Only confirmed registrations can check in.
        if (
            registration.registration_status
            != RegistrationStatus.CONFIRMED
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only confirmed registrations can check in",
            )

        # Prevent duplicate check-in.
        existing_check_in = (
            CheckInRepository.get_by_registration(
                db,
                registration_id,
            )
        )

        if existing_check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration has already been checked in",
            )

        check_in = CheckIn(
            registration_id=registration_id,
            check_in_time=datetime.utcnow(),
            check_in_method=check_in_method,
        )

        return CheckInRepository.create(
            db,
            check_in,
        )

    @staticmethod
    def check_out(
        db: Session,
        registration_id: int,
        current_user: User,
    ):

        # Only Admin, Event Organizer, and Staff
        # can check out attendees.
        CheckInService._validate_staff_role(
            current_user,
        )

        registration = (
            db.query(Registration)
            .filter(
                Registration.id == registration_id,
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )

        check_in = (
            CheckInRepository.get_by_registration(
                db,
                registration_id,
            )
        )

        # Check-out is only possible after check-in.
        if not check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendee has not checked in",
            )

        # Prevent duplicate check-out.
        if check_in.check_out_time is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration has already been checked out",
            )

        check_in.check_out_time = datetime.utcnow()

        return CheckInRepository.update(
            db,
            check_in,
        )

    @staticmethod
    def get_event_attendance(
        db: Session,
        event_id: int,
        current_user: User,
    ):

        # Only Admin, Event Organizer, and Staff
        # can view attendance history.
        CheckInService._validate_staff_role(
            current_user,
        )

        return CheckInRepository.get_by_event(
            db,
            event_id,
        )