from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
)
from services.session_service import SessionService
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SessionService.create(
        db,
        payload,
        current_user,
    )


@router.get(
    "",
    response_model=list[SessionResponse],
)
def list_sessions(
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
    ),
    speaker_id: int | None = Query(
        None,
        ge=1,
    ),
    event_id: int | None = Query(
        None,
        ge=1,
    ),
    session_type: str | None = Query(
        None,
    ),
    session_date: datetime | None = Query(
        None,
        description="Filter sessions by date",
    ),
    sort_by: str = Query(
        "start_time",
    ),
    sort_order: str = Query(
        "asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit

    allowed_sort_fields = {
        "id",
        "title",
        "speaker_id",
        "event_id",
        "hall_id",
        "start_time",
        "end_time",
        "capacity",
        "session_type",
    }

    if sort_by not in allowed_sort_fields:
        sort_by = "start_time"

    return SessionService.list_all(
        db=db,
        skip=skip,
        limit=limit,
        speaker_id=speaker_id,
        event_id=event_id,
        session_type=session_type,
        session_date=session_date,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    return SessionService.get_by_id(
        db,
        session_id,
    )


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SessionService.update(
        db,
        session_id,
        payload,
        current_user,
    )


@router.delete(
    "/{session_id}",
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SessionService.delete(
        db,
        session_id,
        current_user,
    )