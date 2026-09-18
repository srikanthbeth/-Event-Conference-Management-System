from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.event import Event
from models.hall import Hall
from models.session import Session as SessionModel
from models.speaker import Speaker
from repositories.session_repository import SessionRepository
from schemas.session import SessionCreate, SessionUpdate
from utils.enums import UserRole


class SessionService:

    MANAGE_ROLES = {
        UserRole.ADMIN,
        UserRole.EVENT_ORGANIZER,
    }

    @staticmethod
    def _check_manage_permission(current_user):
        if current_user.role not in SessionService.MANAGE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage sessions",
            )

        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive users cannot manage sessions",
            )

    @staticmethod
    def _validate_references(
        db: Session,
        payload,
    ):
        event = db.get(
            Event,
            payload.event_id,
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        speaker = db.get(
            Speaker,
            payload.speaker_id,
        )

        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker not found",
            )

        if not speaker.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive speaker cannot be assigned to a session",
            )

        hall = db.get(
            Hall,
            payload.hall_id,
        )

        if not hall:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hall not found",
            )

        if payload.capacity > hall.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session capacity cannot exceed hall capacity",
            )

        return event, speaker, hall

    @staticmethod
    def _validate_event_timing(
        event,
        start_time: datetime,
        end_time: datetime,
    ):
        if start_time < event.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session cannot start before the event starts",
            )

        if end_time > event.end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session cannot end after the event ends",
            )

    @staticmethod
    def _check_overlaps(
        db: Session,
        speaker_id: int,
        hall_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_session_id: int | None = None,
    ):

        query = db.query(SessionModel).filter(
            SessionModel.start_time < end_time,
            SessionModel.end_time > start_time,
        )

        if exclude_session_id is not None:
            query = query.filter(
                SessionModel.id != exclude_session_id
            )

        overlapping_speaker = query.filter(
            SessionModel.speaker_id == speaker_id
        ).first()

        if overlapping_speaker:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Speaker is already assigned to an overlapping session",
            )

        overlapping_hall = query.filter(
            SessionModel.hall_id == hall_id
        ).first()

        if overlapping_hall:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hall is already booked for an overlapping session",
            )

    @staticmethod
    def create(
        db: Session,
        payload: SessionCreate,
        current_user,
    ):

        SessionService._check_manage_permission(
            current_user
        )

        event, speaker, hall = (
            SessionService._validate_references(
                db,
                payload,
            )
        )

        SessionService._validate_event_timing(
            event,
            payload.start_time,
            payload.end_time,
        )

        SessionService._check_overlaps(
            db,
            speaker_id=payload.speaker_id,
            hall_id=payload.hall_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        session = SessionModel(
            event_id=payload.event_id,
            speaker_id=payload.speaker_id,
            hall_id=payload.hall_id,
            title=payload.title,
            description=payload.description,
            start_time=payload.start_time,
            end_time=payload.end_time,
            capacity=payload.capacity,
            session_type=payload.session_type,
        )

        return SessionRepository.create(
            db,
            session,
        )

    @staticmethod
    def list_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        speaker_id: int | None = None,
        event_id: int | None = None,
        session_type: str | None = None,
        session_date: datetime | None = None,
        sort_by: str = "start_time",
        sort_order: str = "asc",
    ):
        return SessionRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            speaker_id=speaker_id,
            event_id=event_id,
            session_type=session_type,
            session_date=session_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @staticmethod
    def get_by_id(
        db: Session,
        session_id: int,
    ):

        session = SessionRepository.get_by_id(
            db,
            session_id,
        )

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return session

    @staticmethod
    def update(
        db: Session,
        session_id: int,
        payload: SessionUpdate,
        current_user,
    ):

        SessionService._check_manage_permission(
            current_user
        )

        session = SessionService.get_by_id(
            db,
            session_id,
        )

        values = payload.model_dump(
            exclude_unset=True
        )

        event_id = values.get(
            "event_id",
            session.event_id,
        )

        speaker_id = values.get(
            "speaker_id",
            session.speaker_id,
        )

        hall_id = values.get(
            "hall_id",
            session.hall_id,
        )

        start_time = values.get(
            "start_time",
            session.start_time,
        )

        end_time = values.get(
            "end_time",
            session.end_time,
        )

        capacity = values.get(
            "capacity",
            session.capacity,
        )

        event = db.get(
            Event,
            event_id,
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        speaker = db.get(
            Speaker,
            speaker_id,
        )

        if not speaker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Speaker not found",
            )

        if not speaker.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive speaker cannot be assigned to a session",
            )

        hall = db.get(
            Hall,
            hall_id,
        )

        if not hall:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hall not found",
            )

        if capacity > hall.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session capacity cannot exceed hall capacity",
            )

        if end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="end_time must be after start_time",
            )

        SessionService._validate_event_timing(
            event,
            start_time,
            end_time,
        )

        SessionService._check_overlaps(
            db,
            speaker_id=speaker_id,
            hall_id=hall_id,
            start_time=start_time,
            end_time=end_time,
            exclude_session_id=session.id,
        )

        return SessionRepository.update(
            db,
            session,
            values,
        )

    @staticmethod
    def delete(
        db: Session,
        session_id: int,
        current_user,
    ):

        SessionService._check_manage_permission(
            current_user
        )

        session = SessionService.get_by_id(
            db,
            session_id,
        )

        SessionRepository.delete(
            db,
            session,
        )

        return {
            "message": "Session deleted successfully"
        }