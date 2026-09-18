from sqlalchemy.orm import Session

from models.attendee import Attendee
from models.user import User
from repositories.attendee_repository import AttendeeRepository


class AttendeeService:

    @staticmethod
    def get_or_create_from_user(
        db: Session,
        user: User,
    ) -> Attendee:

        attendee = AttendeeRepository.get_by_email(
            db,
            user.email,
        )

        if attendee:
            return attendee

        attendee = Attendee(
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
        )

        return AttendeeRepository.create(
            db,
            attendee,
        )