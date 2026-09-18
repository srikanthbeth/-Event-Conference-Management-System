from sqlalchemy.orm import Session

from models.certificate import Certificate
from utils.enums import CertificateStatus


class CertificateRepository:

    @staticmethod
    def create(
        db: Session,
        certificate: Certificate,
    ):
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        return certificate

    @staticmethod
    def get_by_id(
        db: Session,
        certificate_id: int,
    ):
        return (
            db.query(Certificate)
            .filter(Certificate.id == certificate_id)
            .first()
        )

    @staticmethod
    def get_by_registration(
        db: Session,
        registration_id: int,
    ):
        return (
            db.query(Certificate)
            .filter(
                Certificate.registration_id == registration_id
            )
            .first()
        )

    @staticmethod
    def get_by_certificate_number(
        db: Session,
        certificate_number: str,
    ):
        return (
            db.query(Certificate)
            .filter(
                Certificate.certificate_number
                == certificate_number
            )
            .first()
        )

    @staticmethod
    def get_by_attendee(
        db: Session,
        attendee_id: int,
    ):
        return (
            db.query(Certificate)
            .filter(
                Certificate.attendee_id == attendee_id
            )
            .order_by(Certificate.issue_date.desc())
            .all()
        )

    @staticmethod
    def get_by_event(
        db: Session,
        event_id: int,
    ):
        return (
            db.query(Certificate)
            .filter(
                Certificate.event_id == event_id
            )
            .order_by(Certificate.issue_date.desc())
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        certificate: Certificate,
    ):
        db.commit()
        db.refresh(certificate)
        return certificate