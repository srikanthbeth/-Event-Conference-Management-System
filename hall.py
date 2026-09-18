from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import HallAvailabilityStatus


class HallCreate(BaseModel):
    hall_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    capacity: int = Field(
        ...,
        gt=0,
    )

    floor: int = Field(
        ...,
        ge=0,
    )

    availability_status: HallAvailabilityStatus = (
        HallAvailabilityStatus.AVAILABLE
    )


class HallResponse(BaseModel):
    id: int
    venue_id: int
    hall_name: str
    capacity: int
    floor: int
    availability_status: HallAvailabilityStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )