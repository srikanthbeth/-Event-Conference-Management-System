from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.session import Session as SessionModel


class SessionRepository:

    @staticmethod
    def create(
        db: Session,
        session: SessionModel,
    ) -> SessionModel:
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_by_id(
        db: Session,
        session_id: int,
    ) -> SessionModel | None:
        return db.get(SessionModel, session_id)

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        speaker_id: int | None = None,
        event_id: int | None = None,
        session_type: str | None = None,
        session_date: datetime | None = None,
        sort_by: str = "start_time",
        sort_order: str = "asc",
    ) -> list[SessionModel]:

        statement = select(SessionModel)

        if speaker_id is not None:
            statement = statement.where(
                SessionModel.speaker_id == speaker_id
            )

        if event_id is not None:
            statement = statement.where(
                SessionModel.event_id == event_id
            )

        if session_type is not None:
            statement = statement.where(
                SessionModel.session_type == session_type
            )

        if session_date is not None:
            day_start = session_date.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            day_end = day_start + timedelta(days=1)

            statement = statement.where(
                SessionModel.start_time >= day_start,
                SessionModel.start_time < day_end,
            )

        sort_columns = {
            "id": SessionModel.id,
            "title": SessionModel.title,
            "speaker_id": SessionModel.speaker_id,
            "event_id": SessionModel.event_id,
            "hall_id": SessionModel.hall_id,
            "start_time": SessionModel.start_time,
            "end_time": SessionModel.end_time,
            "capacity": SessionModel.capacity,
            "session_type": SessionModel.session_type,
        }

        sort_column = sort_columns.get(
            sort_by,
            SessionModel.start_time,
        )

        if sort_order.lower() == "desc":
            statement = statement.order_by(
                sort_column.desc()
            )
        else:
            statement = statement.order_by(
                sort_column.asc()
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
    def get_by_event(
        db: Session,
        event_id: int,
    ) -> list[SessionModel]:

        statement = (
            select(SessionModel)
            .where(
                SessionModel.event_id == event_id
            )
            .order_by(
                SessionModel.start_time
            )
        )

        return list(
            db.scalars(statement).all()
        )

    @staticmethod
    def update(
        db: Session,
        session: SessionModel,
        values: dict,
    ) -> SessionModel:

        for field, value in values.items():
            setattr(
                session,
                field,
                value,
            )

        db.commit()
        db.refresh(session)

        return session

    @staticmethod
    def delete(
        db: Session,
        session: SessionModel,
    ) -> None:

        db.delete(session)
        db.commit()