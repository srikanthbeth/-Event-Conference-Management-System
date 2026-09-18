from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SessionCreate(BaseModel):
    event_id: int
    speaker_id: int
    hall_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    capacity: int = Field(..., gt=0)
    session_type: str = Field(..., min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class SessionUpdate(BaseModel):
    event_id: int | None = None
    speaker_id: int | None = None
    hall_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = Field(default=None, gt=0)
    session_type: str | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_times(self):
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")

        return self


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    speaker_id: int
    hall_id: int
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    capacity: int
    session_type: str
    created_at: datetime
    updated_at: datetime