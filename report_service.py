from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories.report_repository import ReportRepository
from utils.enums import UserRole


class ReportService:

    @staticmethod
    def _get_organizer_id(current_user):
        if current_user.role == UserRole.ADMIN:
            return None

        if current_user.role == UserRole.EVENT_ORGANIZER:
            return current_user.id

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Event Organizer access required",
        )

    @staticmethod
    def get_daily_registrations(
        db: Session,
        current_user,
    ):
        organizer_id = ReportService._get_organizer_id(
            current_user
        )

        return ReportRepository.get_daily_registrations(
            db,
            organizer_id,
        )

    @staticmethod
    def get_event_revenue(
        db: Session,
        current_user,
    ):
        organizer_id = ReportService._get_organizer_id(
            current_user
        )

        return ReportRepository.get_event_revenue(
            db,
            organizer_id,
        )

    @staticmethod
    def get_ticket_sales(
        db: Session,
        current_user,
    ):
        organizer_id = ReportService._get_organizer_id(
            current_user
        )

        return ReportRepository.get_ticket_sales(
            db,
            organizer_id,
        )

    @staticmethod
    def get_attendance(
        db: Session,
        current_user,
    ):
        organizer_id = ReportService._get_organizer_id(
            current_user
        )

        return ReportRepository.get_attendance(
            db,
            organizer_id,
        )

    @staticmethod
    def get_speaker_ratings(
        db: Session,
        current_user,
    ):
        organizer_id = ReportService._get_organizer_id(
            current_user
        )

        return ReportRepository.get_speaker_ratings(
            db,
            organizer_id,
        )

    @staticmethod
    def get_session_popularity(
        db: Session,
        current_user,
    ):
        organizer_id = ReportService._get_organizer_id(
            current_user
        )

        return ReportRepository.get_session_popularity(
            db,
            organizer_id,
        )