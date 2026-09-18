from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import VenueStatus


class VenueCreate(BaseModel):
    venue_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    address: str = Field(
        ...,
        min_length=2,
        max_length=500,
    )

    city: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    capacity: int = Field(
        ...,
        gt=0,
    )

    facilities: str | None = None

    status: VenueStatus = VenueStatus.ACTIVE


class VenueResponse(BaseModel):
    id: int
    venue_name: str
    address: str
    city: str
    capacity: int
    facilities: str | None
    status: VenueStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )