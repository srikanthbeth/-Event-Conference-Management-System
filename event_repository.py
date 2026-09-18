from datetime import datetime

from sqlalchemy import exists, func
from sqlalchemy.orm import Session

from models.event import Event
from models.hall import Hall
from models.registration import Registration
from models.session import Session as SessionModel
from models.venue import Venue
from utils.enums import EventStatus, RegistrationStatus


class EventRepository:

    @staticmethod
    def create(
        db: Session,
        event: Event,
    ) -> Event:
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_by_id(
        db: Session,
        event_id: int,
    ) -> Event | None:
        return (
            db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        event_type=None,
        city: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        status=None,
        min_available_capacity: int | None = None,
        sort_by: str = "start_date",
        sort_order: str = "asc",
    ) -> list[Event]:

        query = db.query(Event)

        # ---------------------------------------------------------
        # Event type filter
        # ---------------------------------------------------------

        if event_type is not None:
            query = query.filter(
                Event.event_type == event_type
            )

        # ---------------------------------------------------------
        # City filter
        #
        # Event does not have a city column.
        # City is stored in Venue and is reached through:
        #
        # Event -> Session -> Hall -> Venue
        #
        # EXISTS is used so events without matching sessions are
        # not accidentally duplicated.
        # ---------------------------------------------------------

        if city is not None:
            city_value = city.strip().lower()

            city_exists = exists().where(
                SessionModel.event_id == Event.id,
                SessionModel.hall_id == Hall.id,
                Hall.venue_id == Venue.id,
                func.lower(Venue.city) == city_value,
            )

            query = query.filter(city_exists)

        # ---------------------------------------------------------
        # Event start date filter
        # ---------------------------------------------------------

        if start_date is not None:
            query = query.filter(
                Event.start_date >= start_date
            )

        # ---------------------------------------------------------
        # Event end date filter
        # ---------------------------------------------------------

        if end_date is not None:
            query = query.filter(
                Event.end_date <= end_date
            )

        # ---------------------------------------------------------
        # Status filter
        # ---------------------------------------------------------

        if status is not None:
            query = query.filter(
                Event.status == status
            )

        # ---------------------------------------------------------
        # Available capacity filter
        #
        # Available capacity =
        # Event capacity - active registrations
        #
        # Cancelled registrations are excluded.
        # ---------------------------------------------------------

        if min_available_capacity is not None:

            active_registration_count = (
                db.query(
                    func.count(Registration.id)
                )
                .filter(
                    Registration.event_id == Event.id,
                    Registration.registration_status
                    != RegistrationStatus.CANCELLED,
                )
                .correlate(Event)
                .scalar_subquery()
            )

            available_capacity = (
                Event.capacity - active_registration_count
            )

            query = query.filter(
                available_capacity >= min_available_capacity
            )

        # ---------------------------------------------------------
        # Sorting
        # ---------------------------------------------------------

        sort_columns = {
            "id": Event.id,
            "event_name": Event.event_name,
            "event_type": Event.event_type,
            "start_date": Event.start_date,
            "end_date": Event.end_date,
            "registration_start": Event.registration_start,
            "registration_end": Event.registration_end,
            "capacity": Event.capacity,
            "status": Event.status,
        }

        sort_column = sort_columns.get(
            sort_by,
            Event.start_date,
        )

        if sort_order.lower() == "desc":
            query = query.order_by(
                sort_column.desc()
            )
        else:
            query = query.order_by(
                sort_column.asc()
            )

        # ---------------------------------------------------------
        # Pagination
        # ---------------------------------------------------------

        return (
            query
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_organizer(
        db: Session,
        organizer_id: int,
        skip: int = 0,
        limit: int = 100,
        event_type=None,
        city: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        status=None,
        min_available_capacity: int | None = None,
        sort_by: str = "start_date",
        sort_order: str = "asc",
    ) -> list[Event]:

        query = db.query(Event).filter(
            Event.organizer_id == organizer_id
        )

        # ---------------------------------------------------------
        # Event type filter
        # ---------------------------------------------------------

        if event_type is not None:
            query = query.filter(
                Event.event_type == event_type
            )

        # ---------------------------------------------------------
        # City filter through Venue
        # ---------------------------------------------------------

        if city is not None:
            city_value = city.strip().lower()

            city_exists = exists().where(
                SessionModel.event_id == Event.id,
                SessionModel.hall_id == Hall.id,
                Hall.venue_id == Venue.id,
                func.lower(Venue.city) == city_value,
            )

            query = query.filter(city_exists)

        # ---------------------------------------------------------
        # Date filters
        # ---------------------------------------------------------

        if start_date is not None:
            query = query.filter(
                Event.start_date >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Event.end_date <= end_date
            )

        # ---------------------------------------------------------
        # Status filter
        # ---------------------------------------------------------

        if status is not None:
            query = query.filter(
                Event.status == status
            )

        # ---------------------------------------------------------
        # Available capacity
        # ---------------------------------------------------------

        if min_available_capacity is not None:

            active_registration_count = (
                db.query(
                    func.count(Registration.id)
                )
                .filter(
                    Registration.event_id == Event.id,
                    Registration.registration_status
                    != RegistrationStatus.CANCELLED,
                )
                .correlate(Event)
                .scalar_subquery()
            )

            available_capacity = (
                Event.capacity - active_registration_count
            )

            query = query.filter(
                available_capacity >= min_available_capacity
            )

        # ---------------------------------------------------------
        # Sorting
        # ---------------------------------------------------------

        sort_columns = {
            "id": Event.id,
            "event_name": Event.event_name,
            "event_type": Event.event_type,
            "start_date": Event.start_date,
            "end_date": Event.end_date,
            "registration_start": Event.registration_start,
            "registration_end": Event.registration_end,
            "capacity": Event.capacity,
            "status": Event.status,
        }

        sort_column = sort_columns.get(
            sort_by,
            Event.start_date,
        )

        if sort_order.lower() == "desc":
            query = query.order_by(
                sort_column.desc()
            )
        else:
            query = query.order_by(
                sort_column.asc()
            )

        return (
            query
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        event: Event,
    ) -> Event:
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def delete(
        db: Session,
        event: Event,
    ) -> None:
        db.delete(event)
        db.commit()