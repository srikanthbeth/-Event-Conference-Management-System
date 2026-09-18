from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.dashboard_repository import DashboardRepository
from utils.enums import UserRole


class DashboardService:

    @staticmethod
    def get_admin_dashboard(
        db: Session,
        current_user,
    ):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required",
            )

        return DashboardRepository.get_admin_dashboard(db)

    @staticmethod
    def get_organizer_dashboard(
        db: Session,
        current_user,
    ):
        if current_user.role not in {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Event Organizer access required",
            )

        return DashboardRepository.get_organizer_dashboard(
            db,
            current_user.id,
        )