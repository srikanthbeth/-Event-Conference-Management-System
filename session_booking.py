from datetime import datetime

from pydantic import BaseModel, ConfigDict

from utils.enums import SessionBookingStatus


class SessionBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attendee_id: int
    session_id: int
    booking_date: datetime
    booking_status: SessionBookingStatus