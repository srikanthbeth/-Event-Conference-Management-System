from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.attendee import Attendee
from models.certificate import Certificate
from models.checkin import CheckIn
from models.event import Event
from models.registration import Registration
from models.user import User

from repositories.certificate_repository import (
    CertificateRepository,
)

from utils.enums import (
    CertificateStatus,
    CertificateType,
    RegistrationStatus,
    UserRole,
)


class CertificateService:

    @staticmethod
    def _validate_staff_role(
        current_user: User,
    ):
        allowed_roles = {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        }

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage certificates",
            )

    @staticmethod
    def _generate_certificate_number(
        db: Session,
    ):
        year = datetime.utcnow().year

        certificates = (
            db.query(Certificate)
            .filter(
                Certificate.certificate_number.like(
                    f"CERT-{year}-%"
                )
            )
            .count()
        )

        number = certificates + 1

        certificate_number = (
            f"CERT-{year}-{number:06d}"
        )

        while CertificateRepository.get_by_certificate_number(
            db,
            certificate_number,
        ):
            number += 1
            certificate_number = (
                f"CERT-{year}-{number:06d}"
            )

        return certificate_number

    @staticmethod
    def generate_certificate(
        db: Session,
        registration_id: int,
        certificate_type: CertificateType,
        current_user: User,
    ):
        CertificateService._validate_staff_role(
            current_user
        )

        registration = (
            db.query(Registration)
            .filter(
                Registration.id == registration_id
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )

        if registration.registration_status not in {
            RegistrationStatus.CONFIRMED,
            RegistrationStatus.ATTENDED,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only confirmed or attended registrations "
                    "can receive certificates"
                ),
            )

        check_in = (
            db.query(CheckIn)
            .filter(
                CheckIn.registration_id == registration_id
            )
            .first()
        )

        if not check_in:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Attendee must check in before "
                    "receiving a certificate"
                ),
            )

        existing_certificate = (
            CertificateRepository.get_by_registration(
                db,
                registration_id,
            )
        )

        if existing_certificate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Certificate already exists for this registration",
            )

        event = (
            db.query(Event)
            .filter(
                Event.id == registration.event_id
            )
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        attendee = (
            db.query(Attendee)
            .filter(
                Attendee.id == registration.attendee_id
            )
            .first()
        )

        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendee not found",
            )

        certificate = Certificate(
            certificate_number=(
                CertificateService._generate_certificate_number(
                    db
                )
            ),
            registration_id=registration.id,
            event_id=registration.event_id,
            attendee_id=registration.attendee_id,
            issue_date=datetime.utcnow(),
            certificate_type=certificate_type,
            status=CertificateStatus.ISSUED,
        )

        return CertificateRepository.create(
            db,
            certificate,
        )

    @staticmethod
    def get_certificate(
        db: Session,
        certificate_id: int,
        current_user: User,
    ):
        certificate = (
            CertificateRepository.get_by_id(
                db,
                certificate_id,
            )
        )

        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found",
            )

        if current_user.role == UserRole.ATTENDEE:
            registration = (
                db.query(Registration)
                .filter(
                    Registration.id
                    == certificate.registration_id
                )
                .first()
            )

            if (
                not registration
                or registration.attendee_id
                != current_user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own certificate",
                )

        elif current_user.role not in {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view certificates",
            )

        return certificate

    @staticmethod
    def get_attendee_certificates(
        db: Session,
        attendee_id: int,
        current_user: User,
    ):
        attendee = (
            db.query(Attendee)
            .filter(
                Attendee.id == attendee_id
            )
            .first()
        )

        if not attendee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendee not found",
            )

        if current_user.role == UserRole.ATTENDEE:
            if current_user.id != attendee_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only view your own certificates",
                )

        elif current_user.role not in {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
            UserRole.STAFF,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view certificates",
            )

        return CertificateRepository.get_by_attendee(
            db,
            attendee_id,
        )

    @staticmethod
    def get_event_certificates(
        db: Session,
        event_id: int,
        current_user: User,
    ):
        CertificateService._validate_staff_role(
            current_user
        )

        event = (
            db.query(Event)
            .filter(
                Event.id == event_id
            )
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        return CertificateRepository.get_by_event(
            db,
            event_id,
        )