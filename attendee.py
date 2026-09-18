from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttendeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str | None
    organization: str | None
    designation: str | None
    created_at: datetime
    updated_at: datetime