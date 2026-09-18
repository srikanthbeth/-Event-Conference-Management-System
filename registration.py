from datetime import datetime

from pydantic import BaseModel, ConfigDict

from utils.enums import RegistrationStatus


class RegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    attendee_id: int
    event_id: int
    registration_date: datetime
    registration_status: RegistrationStatus