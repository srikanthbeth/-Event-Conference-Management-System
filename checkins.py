from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.checkin import CheckInResponse
from services.checkin_service import CheckInService
from utils.dependencies import get_current_user
from utils.enums import CheckInMethod


router = APIRouter(
    tags=["Event Check-In"],
)


@router.post(
    "/registrations/{registration_id}/check-in",
    response_model=CheckInResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_in(
    registration_id: int,
    check_in_method: CheckInMethod = Query(
        ...,
        description="Check-in method: QR Code, Manual, or Staff",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CheckInService.check_in(
        db=db,
        registration_id=registration_id,
        check_in_method=check_in_method,
        current_user=current_user,
    )


@router.post(
    "/registrations/{registration_id}/check-out",
    response_model=CheckInResponse,
)
def check_out(
    registration_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CheckInService.check_out(
        db=db,
        registration_id=registration_id,
        current_user=current_user,
    )


@router.get(
    "/events/{event_id}/attendance",
    response_model=list[CheckInResponse],
)
def get_event_attendance(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CheckInService.get_event_attendance(
        db=db,
        event_id=event_id,
        current_user=current_user,
    )