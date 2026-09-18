from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DailyRegistrationReport(BaseModel):
    date: date
    registrations: int


class EventRevenueReport(BaseModel):
    event_id: int
    event_name: str
    revenue: Decimal


class TicketSalesReport(BaseModel):
    event_id: int
    event_name: str
    ticket_id: int
    ticket_type: str
    tickets_sold: int
    revenue: Decimal


class AttendanceReport(BaseModel):
    event_id: int
    event_name: str
    registrations: int
    attendance: int


class SpeakerRatingReport(BaseModel):
    speaker_id: int
    speaker_name: str
    average_rating: float | None
    rating_count: int


class SessionPopularityReport(BaseModel):
    session_id: int
    session_title: str
    event_id: int
    event_name: str
    booking_count: int