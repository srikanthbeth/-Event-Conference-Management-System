from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.registration import Registration
from utils.enums import RegistrationStatus


class RegistrationRepository:

    @staticmethod
    def create(
        db: Session,
        registration: Registration,
    ) -> Registration:

        db.add(registration)
        db.commit()
        db.refresh(registration)

        return registration

    @staticmethod
    def get_by_id(
        db: Session,
        registration_id: int,
    ) -> Registration | None:

        return db.get(
            Registration,
            registration_id,
        )

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        event_id: int | None = None,
        registration_status=None,
        registration_date: datetime | None = None,
        sort_by: str = "registration_date",
        sort_order: str = "desc",
    ) -> list[Registration]:

        statement = select(
            Registration
        )

        if event_id is not None:
            statement = statement.where(
                Registration.event_id == event_id
            )

        if registration_status is not None:
            statement = statement.where(
                Registration.registration_status
                == registration_status
            )

        if registration_date is not None:
            day_start = registration_date.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            from datetime import timedelta

            day_end = day_start + timedelta(days=1)

            statement = statement.where(
                Registration.registration_date >= day_start,
                Registration.registration_date < day_end,
            )

        sort_columns = {
            "id": Registration.id,
            "attendee_id": Registration.attendee_id,
            "event_id": Registration.event_id,
            "registration_date": Registration.registration_date,
            "registration_status": (
                Registration.registration_status
            ),
        }

        sort_column = sort_columns.get(
            sort_by,
            Registration.registration_date,
        )

        if sort_order.lower() == "asc":
            statement = statement.order_by(
                sort_column.asc()
            )
        else:
            statement = statement.order_by(
                sort_column.desc()
            )

        statement = (
            statement
            .offset(skip)
            .limit(limit)
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def get_by_attendee_and_event(
        db: Session,
        attendee_id: int,
        event_id: int,
    ) -> Registration | None:

        statement = select(
            Registration
        ).where(
            Registration.attendee_id == attendee_id,
            Registration.event_id == event_id,
        )

        return db.scalars(
            statement
        ).first()

    @staticmethod
    def count_active_for_event(
        db: Session,
        event_id: int,
    ) -> int:

        statement = select(
            func.count(Registration.id)
        ).where(
            Registration.event_id == event_id,
            Registration.registration_status
            != RegistrationStatus.CANCELLED,
        )

        return db.scalar(statement) or 0

    @staticmethod
    def update(
        db: Session,
        registration: Registration,
        values: dict,
    ) -> Registration:

        for field, value in values.items():
            setattr(
                registration,
                field,
                value,
            )

        db.commit()
        db.refresh(registration)

        return registration