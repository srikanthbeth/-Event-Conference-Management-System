from sqlalchemy.orm import Session

from models.speaker import Speaker


class SpeakerRepository:

    @staticmethod
    def create(
        db: Session,
        speaker: Speaker,
    ) -> Speaker:
        db.add(speaker)
        db.commit()
        db.refresh(speaker)
        return speaker

    @staticmethod
    def get_by_id(
        db: Session,
        speaker_id: int,
    ) -> Speaker | None:
        return (
            db.query(Speaker)
            .filter(Speaker.id == speaker_id)
            .first()
        )

    @staticmethod
    def get_by_email(
        db: Session,
        email: str,
    ) -> Speaker | None:
        return (
            db.query(Speaker)
            .filter(Speaker.email == email)
            .first()
        )

    @staticmethod
    def get_all(
        db: Session,
    ) -> list[Speaker]:
        return (
            db.query(Speaker)
            .order_by(Speaker.id.asc())
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        speaker: Speaker,
    ) -> Speaker:
        db.commit()
        db.refresh(speaker)
        return speaker