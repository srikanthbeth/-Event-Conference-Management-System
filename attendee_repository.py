from sqlalchemy import select
from sqlalchemy.orm import Session

from models.attendee import Attendee


class AttendeeRepository:

    @staticmethod
    def create(
        db: Session,
        attendee: Attendee,
    ) -> Attendee:
        db.add(attendee)
        db.commit()
        db.refresh(attendee)
        return attendee

    @staticmethod
    def get_by_id(
        db: Session,
        attendee_id: int,
    ) -> Attendee | None:
        return db.get(Attendee, attendee_id)

    @staticmethod
    def get_by_email(
        db: Session,
        email: str,
    ) -> Attendee | None:
        statement = select(Attendee).where(
            Attendee.email == email
        )

        return db.scalars(statement).first()

    @staticmethod
    def update(
        db: Session,
        attendee: Attendee,
        values: dict,
    ) -> Attendee:
        for field, value in values.items():
            setattr(attendee, field, value)

        db.commit()
        db.refresh(attendee)

        return attendee