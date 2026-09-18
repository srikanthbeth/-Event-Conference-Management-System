from sqlalchemy.orm import Session

from models.feedback import Feedback


class FeedbackRepository:

    @staticmethod
    def create(
        db: Session,
        feedback: Feedback,
    ) -> Feedback:
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback

    @staticmethod
    def get_by_id(
        db: Session,
        feedback_id: int,
    ) -> Feedback | None:
        return (
            db.query(Feedback)
            .filter(
                Feedback.id == feedback_id
            )
            .first()
        )

    @staticmethod
    def get_by_registration(
        db: Session,
        registration_id: int,
    ) -> list[Feedback]:
        return (
            db.query(Feedback)
            .filter(
                Feedback.registration_id
                == registration_id
            )
            .all()
        )

    @staticmethod
    def get_by_registration_and_session(
        db: Session,
        registration_id: int,
        session_id: int,
    ) -> Feedback | None:
        return (
            db.query(Feedback)
            .filter(
                Feedback.registration_id
                == registration_id,
                Feedback.session_id
                == session_id,
            )
            .first()
        )

    @staticmethod
    def get_by_session(
        db: Session,
        session_id: int,
    ) -> Feedback | None:
        return (
            db.query(Feedback)
            .filter(
                Feedback.session_id
                == session_id
            )
            .first()
        )

    @staticmethod
    def get_by_event(
        db: Session,
        event_id: int,
    ) -> list[Feedback]:
        return (
            db.query(Feedback)
            .filter(
                Feedback.event_id
                == event_id
            )
            .all()
        )

    @staticmethod
    def get_by_speaker(
        db: Session,
        speaker_id: int,
    ) -> list[Feedback]:
        return (
            db.query(Feedback)
            .filter(
                Feedback.speaker_id
                == speaker_id
            )
            .all()
        )