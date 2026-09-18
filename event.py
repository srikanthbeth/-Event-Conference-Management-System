from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from utils.enums import EventStatus, EventType


class EventBase(BaseModel):
    event_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str | None = None

    event_type: EventType

    start_date: datetime

    end_date: datetime

    registration_start: datetime

    registration_end: datetime

    capacity: int = Field(
        ...,
        gt=0,
    )

    status: EventStatus = EventStatus.DRAFT

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError(
                "Event end date must be after event start date"
            )

        if self.registration_end > self.start_date:
            raise ValueError(
                "Registration end must be before or equal to event start"
            )

        if self.registration_end <= self.registration_start:
            raise ValueError(
                "Registration end must be after registration start"
            )

        return self


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    event_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    description: str | None = None

    event_type: EventType | None = None

    start_date: datetime | None = None

    end_date: datetime | None = None

    registration_start: datetime | None = None

    registration_end: datetime | None = None

    capacity: int | None = Field(
        default=None,
        gt=0,
    )

    status: EventStatus | None = None


class EventResponse(EventBase):
    id: int
    organizer_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )