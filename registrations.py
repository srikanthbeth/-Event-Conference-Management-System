from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.registration import RegistrationResponse
from services.registration_service import RegistrationService
from utils.dependencies import get_current_user
from utils.enums import RegistrationStatus


router = APIRouter(
    tags=["Registrations"],
)


@router.post(
    "/events/{event_id}/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_for_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RegistrationService.register(
        db,
        event_id,
        current_user,
    )


@router.get(
    "/registrations",
    response_model=list[RegistrationResponse],
)
def list_registrations(
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
    ),
    event_id: int | None = Query(
        None,
        ge=1,
    ),
    status_filter: RegistrationStatus | None = Query(
        None,
        alias="status",
    ),
    registration_date: datetime | None = Query(
        None,
        description="Filter registrations by date",
    ),
    sort_by: str = Query(
        "registration_date",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit

    allowed_sort_fields = {
        "id",
        "attendee_id",
        "event_id",
        "registration_date",
        "registration_status",
    }

    if sort_by not in allowed_sort_fields:
        sort_by = "registration_date"

    return RegistrationService.list_all(
        db=db,
        skip=skip,
        limit=limit,
        event_id=event_id,
        registration_status=status_filter,
        registration_date=registration_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/registrations/{registration_id}",
    response_model=RegistrationResponse,
)
def get_registration(
    registration_id: int,
    db: Session = Depends(get_db),
):
    return RegistrationService.get_by_id(
        db,
        registration_id,
    )


@router.post(
    "/registrations/{registration_id}/cancel",
    response_model=RegistrationResponse,
)
def cancel_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RegistrationService.cancel(
        db,
        registration_id,
        current_user,
    )