from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.notification import NotificationResponse
from services.notification_service import (
    NotificationService,
)
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def get_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.get_user_notifications(
        db,
        current_user,
    )


@router.get(
    "/unread",
    response_model=list[NotificationResponse],
)
def get_unread_notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.get_unread_notifications(
        db,
        current_user,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.get_notification(
        db,
        notification_id,
        current_user,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return NotificationService.mark_as_read(
        db,
        notification_id,
        current_user,
    )