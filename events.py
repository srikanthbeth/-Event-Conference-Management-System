from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.event import (
    EventCreate,
    EventResponse,
    EventUpdate,
)
from services.event_service import EventService
from utils.dependencies import get_current_user
from utils.enums import EventStatus, EventType


router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EventService.create_event(
        db,
        current_user,
        event_data,
    )


@router.get(
    "",
    response_model=list[EventResponse],
)
def list_events(
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
        description="Number of records per page",
    ),
    event_type: EventType | None = Query(
        None,
        description="Filter by event type",
    ),
    city: str | None = Query(
        None,
        description="Filter by city",
    ),
    start_date: datetime | None = Query(
        None,
        description="Filter events starting on or after this date",
    ),
    end_date: datetime | None = Query(
        None,
        description="Filter events starting on or before this date",
    ),
    status_filter: EventStatus | None = Query(
        None,
        alias="status",
        description="Filter by event status",
    ),
    min_available_capacity: int | None = Query(
        None,
        ge=0,
        description="Minimum available event capacity",
    ),
    sort_by: str = Query(
        "start_date",
        description="Sort field",
    ),
    sort_order: str = Query(
        "asc",
        pattern="^(asc|desc)$",
        description="Sort direction",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skip = (page - 1) * limit

    allowed_sort_fields = {
        "id",
        "event_name",
        "event_type",
        "start_date",
        "end_date",
        "registration_start",
        "registration_end",
        "capacity",
        "status",
    }

    if sort_by not in allowed_sort_fields:
        sort_by = "start_date"

    return EventService.list_events(
        db=db,
        current_user=current_user,
        skip=skip,
        limit=limit,
        event_type=event_type,
        city=city,
        start_date=start_date,
        end_date=end_date,
        status=status_filter,
        min_available_capacity=min_available_capacity,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EventService.get_event(
        db,
        event_id,
    )


@router.put(
    "/{event_id}",
    response_model=EventResponse,
)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EventService.update_event(
        db,
        current_user,
        event_id,
        event_data,
    )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    EventService.delete_event(
        db,
        current_user,
        event_id,
    )