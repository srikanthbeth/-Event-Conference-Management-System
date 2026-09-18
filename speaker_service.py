from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.speaker import Speaker
from models.user import User
from repositories.speaker_repository import SpeakerRepository
from schemas.speaker import SpeakerCreate, SpeakerUpdate
from utils.enums import UserRole


class SpeakerService:

    @staticmethod
    def _check_management_permission(
        current_user: User,
    ) -> None:
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user cannot manage speakers",
            )

        allowed_roles = {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
        }

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage speakers",
            )

    @staticmethod
    def create_speaker(
        db: Session,
        current_user: User,
        speaker_data: SpeakerCreate,
    ) -> Speaker:

        SpeakerService._check_management_permission(
            current_user
        )

        existing_speaker = SpeakerRepository.get_by_email(
            db,
            str(speaker_data.email),
        )

        if existing_speaker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Speaker with this email already exists",
            )

        speaker = Speaker(
            name=speaker_data.name,
            email=str(speaker_data.email),
            phone=speaker_data.phone,
            bio=speaker_data.bio,
            expertise=speaker_data.expertise,
            company=speaker_data.company,
            experience=speaker_data.experience,
            is_active=True,
        )

        return SpeakerRepository.create(db, speaker)

    @staticmethod
    def list_speakers(
        db: Session,
    ) -> list[Speaker]:
        return SpeakerRepository.get_all(db)

    @staticmethod
    def get_speaker(
        db: Session,
        speaker_id: int,
    ) -> Speaker:

        speaker = SpeakerRepository.get_by_id(
            db,
            speaker_id,
        )

        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker not found",
            )

        return speaker

    @staticmethod
    def update_speaker(
        db: Session,
        current_user: User,
        speaker_id: int,
        speaker_data: SpeakerUpdate,
    ) -> Speaker:

        SpeakerService._check_management_permission(
            current_user
        )

        speaker = SpeakerRepository.get_by_id(
            db,
            speaker_id,
        )

        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker not found",
            )

        if speaker_data.email is not None:
            existing_speaker = SpeakerRepository.get_by_email(
                db,
                str(speaker_data.email),
            )

            if (
                existing_speaker
                and existing_speaker.id != speaker.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Speaker with this email already exists",
                )

            speaker.email = str(speaker_data.email)

        if speaker_data.name is not None:
            speaker.name = speaker_data.name

        if speaker_data.phone is not None:
            speaker.phone = speaker_data.phone

        if speaker_data.bio is not None:
            speaker.bio = speaker_data.bio

        if speaker_data.expertise is not None:
            speaker.expertise = speaker_data.expertise

        if speaker_data.company is not None:
            speaker.company = speaker_data.company

        if speaker_data.experience is not None:
            speaker.experience = speaker_data.experience

        if speaker_data.is_active is not None:
            speaker.is_active = speaker_data.is_active

        return SpeakerRepository.update(db, speaker)