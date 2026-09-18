from decimal import Decimal

from pydantic import BaseModel


class AdminDashboardResponse(BaseModel):
    total_events: int
    active_events: int
    completed_events: int
    total_attendees: int
    total_registrations: int
    total_tickets_sold: int
    total_revenue: Decimal
    total_refunds: Decimal
    average_event_rating: float | None


class SpeakerPerformance(BaseModel):
    speaker_id: int
    speaker_name: str
    average_rating: float | None
    feedback_count: int


class SessionPopularity(BaseModel):
    session_id: int
    session_title: str
    booking_count: int


class OrganizerDashboardResponse(BaseModel):
    event_registrations: int
    ticket_sales: int
    revenue: Decimal
    attendance: int
    session_bookings: int
    speaker_performance: list[SpeakerPerformance]
    session_popularity: list[SessionPopularity]