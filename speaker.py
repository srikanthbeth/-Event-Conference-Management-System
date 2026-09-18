from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SpeakerCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    bio: str | None = None

    expertise: str = Field(
        ...,
        min_length=2,
        max_length=255,
    )

    company: str | None = Field(
        default=None,
        max_length=200,
    )

    experience: int | None = Field(
        default=None,
        ge=0,
    )


class SpeakerUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    bio: str | None = None

    expertise: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    company: str | None = Field(
        default=None,
        max_length=200,
    )

    experience: int | None = Field(
        default=None,
        ge=0,
    )

    is_active: bool | None = None


class SpeakerResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None
    bio: str | None
    expertise: str
    company: str | None
    experience: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )