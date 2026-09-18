from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.speaker import (
    SpeakerCreate,
    SpeakerResponse,
    SpeakerUpdate,
)
from services.speaker_service import SpeakerService
from utils.dependencies import get_current_user


router = APIRouter(
    prefix="/speakers",
    tags=["Speakers"],
)


@router.post(
    "",
    response_model=SpeakerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_speaker(
    speaker_data: SpeakerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SpeakerService.create_speaker(
        db,
        current_user,
        speaker_data,
    )


@router.get(
    "",
    response_model=list[SpeakerResponse],
)
def list_speakers(
    db: Session = Depends(get_db),
):
    return SpeakerService.list_speakers(db)


@router.get(
    "/{speaker_id}",
    response_model=SpeakerResponse,
)
def get_speaker(
    speaker_id: int,
    db: Session = Depends(get_db),
):
    return SpeakerService.get_speaker(
        db,
        speaker_id,
    )


@router.put(
    "/{speaker_id}",
    response_model=SpeakerResponse,
)
def update_speaker(
    speaker_id: int,
    speaker_data: SpeakerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return SpeakerService.update_speaker(
        db,
        current_user,
        speaker_id,
        speaker_data,
    )