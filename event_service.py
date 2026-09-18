from datetime import datetime

from sqlalchemy.orm import Session

from models.event import Event
from models.user import User
from repositories.event_repository import EventRepository
from utils.enums import EventStatus, UserRole
from utils.exceptions import bad_request, forbidden, not_found


class EventService:

    @staticmethod
    def create_event(
        db: Session,
        current_user: User,
        event_data,
    ) -> Event:

        if current_user.role not in (
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
        ):
            raise forbidden(
                "Only Admin or Event Organizer can create events"
            )

        if not current_user.is_active:
            raise forbidden(
                "Inactive users cannot create events"
            )

        organizer_id = current_user.id

        event = Event(
            event_name=event_data.event_name,
            description=event_data.description,
            event_type=event_data.event_type,
            organizer_id=organizer_id,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            registration_start=event_data.registration_start,
            registration_end=event_data.registration_end,
            capacity=event_data.capacity,
            status=event_data.status,
        )

        return EventRepository.create(
            db,
            event,
        )

    @staticmethod
    def get_event(
        db: Session,
        event_id: int,
    ) -> Event:

        event = EventRepository.get_by_id(
            db,
            event_id,
        )

        if not event:
            raise not_found(
                "Event not found"
            )

        return event

    @staticmethod
    def list_events(
        db: Session,
        current_user: User,
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
    ):

        if current_user.role == UserRole.EVENT_ORGANIZER:
            return EventRepository.get_by_organizer(
                db=db,
                organizer_id=current_user.id,
                skip=skip,
                limit=limit,
                event_type=event_type,
                city=city,
                start_date=start_date,
                end_date=end_date,
                status=status,
                min_available_capacity=min_available_capacity,
                sort_by=sort_by,
                sort_order=sort_order,
            )

        return EventRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            event_type=event_type,
            city=city,
            start_date=start_date,
            end_date=end_date,
            status=status,
            min_available_capacity=min_available_capacity,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    def update_event(
        db: Session,
        current_user: User,
        event_id: int,
        event_data,
    ) -> Event:

        event = EventService.get_event(
            db,
            event_id,
        )

        if (
            current_user.role != UserRole.ADMIN
            and event.organizer_id != current_user.id
        ):
            raise forbidden(
                "You can only modify your own events"
            )

        update_data = event_data.model_dump(
            exclude_unset=True
        )

        start_date = update_data.get(
            "start_date",
            event.start_date,
        )

        end_date = update_data.get(
            "end_date",
            event.end_date,
        )

        registration_start = update_data.get(
            "registration_start",
            event.registration_start,
        )

        registration_end = update_data.get(
            "registration_end",
            event.registration_end,
        )

        capacity = update_data.get(
            "capacity",
            event.capacity,
        )

        if end_date <= start_date:
            raise bad_request(
                "Event end date must be after event start date"
            )

        if registration_end > start_date:
            raise bad_request(
                "Registration end must be before or equal to event start"
            )

        if registration_end <= registration_start:
            raise bad_request(
                "Registration end must be after registration start"
            )

        if capacity <= 0:
            raise bad_request(
                "Capacity must be greater than 0"
            )

        if (
            update_data.get("status")
            == EventStatus.REGISTRATION_OPEN
            and event.status == EventStatus.CANCELLED
        ):
            raise bad_request(
                "Cancelled events cannot accept registrations"
            )

        for field, value in update_data.items():
            setattr(
                event,
                field,
                value,
            )

        return EventRepository.update(
            db,
            event,
        )

    @staticmethod
    def delete_event(
        db: Session,
        current_user: User,
        event_id: int,
    ) -> None:

        event = EventService.get_event(
            db,
            event_id,
        )

        if (
            current_user.role != UserRole.ADMIN
            and event.organizer_id != current_user.id
        ):
            raise forbidden(
                "You can only delete your own events"
            )

        EventRepository.delete(
            db,
            event,
        )