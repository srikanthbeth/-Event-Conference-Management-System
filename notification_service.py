from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.notification import Notification
from repositories.notification_repository import (
    NotificationRepository,
)


class NotificationService:

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
    ):
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            is_read=False,
        )

        return NotificationRepository.create(
            db,
            notification,
        )

    @staticmethod
    def get_notification(
        db: Session,
        notification_id: int,
        current_user,
    ):
        notification = (
            NotificationRepository.get_by_id(
                db,
                notification_id,
            )
        )

        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        if notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own notifications",
            )

        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        current_user,
    ):
        return NotificationRepository.get_by_user(
            db,
            current_user.id,
        )

    @staticmethod
    def get_unread_notifications(
        db: Session,
        current_user,
    ):
        return NotificationRepository.get_unread_by_user(
            db,
            current_user.id,
        )

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: int,
        current_user,
    ):
        notification = (
            NotificationService.get_notification(
                db,
                notification_id,
                current_user,
            )
        )

        return NotificationRepository.mark_as_read(
            db,
            notification,
        )