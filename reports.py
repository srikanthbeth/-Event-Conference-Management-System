from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.report import (
    AttendanceReport,
    DailyRegistrationReport,
    EventRevenueReport,
    SessionPopularityReport,
    SpeakerRatingReport,
    TicketSalesReport,
)
from services.report_service import ReportService
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/daily-registrations",
    response_model=list[DailyRegistrationReport],
)
def daily_registration_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReportService.get_daily_registrations(
        db,
        current_user,
    )


@router.get(
    "/event-revenue",
    response_model=list[EventRevenueReport],
)
def event_revenue_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReportService.get_event_revenue(
        db,
        current_user,
    )


@router.get(
    "/ticket-sales",
    response_model=list[TicketSalesReport],
)
def ticket_sales_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = ReportService.get_ticket_sales(
        db,
        current_user,
    )

    return [
        {
            "event_id": row.event_id,
            "event_name": row.event_name,
            "ticket_id": row.ticket_id,
            "ticket_type": (
                row.ticket_type.value
                if hasattr(row.ticket_type, "value")
                else str(row.ticket_type)
            ),
            "tickets_sold": int(row.tickets_sold),
            "revenue": row.revenue,
        }
        for row in rows
    ]


@router.get(
    "/attendance",
    response_model=list[AttendanceReport],
)
def attendance_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReportService.get_attendance(
        db,
        current_user,
    )


@router.get(
    "/speaker-ratings",
    response_model=list[SpeakerRatingReport],
)
def speaker_rating_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = ReportService.get_speaker_ratings(
        db,
        current_user,
    )

    return [
        {
            "speaker_id": row.speaker_id,
            "speaker_name": row.speaker_name,
            "average_rating": (
                round(float(row.average_rating), 2)
                if row.average_rating is not None
                else None
            ),
            "rating_count": row.rating_count,
        }
        for row in rows
    ]


@router.get(
    "/session-popularity",
    response_model=list[SessionPopularityReport],
)
def session_popularity_report(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ReportService.get_session_popularity(
        db,
        current_user,
    )