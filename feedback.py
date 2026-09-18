from pydantic import BaseModel, ConfigDict, Field


class FeedbackCreate(BaseModel):
    registration_id: int
    event_id: int
    speaker_id: int | None = None
    session_id: int | None = None
    rating: int = Field(..., ge=1, le=5)
    feedback: str | None = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration_id: int
    event_id: int
    speaker_id: int | None
    session_id: int | None
    rating: int
    feedback: str | None