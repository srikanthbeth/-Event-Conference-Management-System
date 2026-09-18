from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User

from schemas.session_booking import (
    SessionBookingResponse,
)

from services.session_booking_service import (
    SessionBookingService,
)

from utils.dependencies import get_current_user


router = APIRouter(
    tags=["Session Bookings"],
)


@router.post(
    "/sessions/{session_id}/book",
    response_model=SessionBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
def book_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return SessionBookingService.book_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )


@router.get(
    "/attendees/{attendee_id}/sessions",
    response_model=list[SessionBookingResponse],
)
def get_attendee_sessions(
    attendee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return SessionBookingService.get_attendee_sessions(
        db=db,
        attendee_id=attendee_id,
        current_user=current_user,
    )


@router.delete(
    "/session-bookings/{booking_id}",
)
def delete_session_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return SessionBookingService.cancel_booking(
        db=db,
        booking_id=booking_id,
        current_user=current_user,
    )