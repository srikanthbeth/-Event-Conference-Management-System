from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.certificate import (
    CertificateCreate,
    CertificateResponse,
)
from services.certificate_service import (
    CertificateService,
)
from utils.dependencies import get_current_user


router = APIRouter(
    tags=["Certificates"]
)


@router.post(
    "/registrations/{registration_id}/certificate",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_certificate(
    registration_id: int,
    payload: CertificateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CertificateService.generate_certificate(
        db=db,
        registration_id=registration_id,
        certificate_type=payload.certificate_type,
        current_user=current_user,
    )


@router.get(
    "/certificates/{certificate_id}",
    response_model=CertificateResponse,
)
def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CertificateService.get_certificate(
        db=db,
        certificate_id=certificate_id,
        current_user=current_user,
    )


@router.get(
    "/attendees/{attendee_id}/certificates",
    response_model=list[CertificateResponse],
)
def get_attendee_certificates(
    attendee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CertificateService.get_attendee_certificates(
        db=db,
        attendee_id=attendee_id,
        current_user=current_user,
    )


@router.get(
    "/events/{event_id}/certificates",
    response_model=list[CertificateResponse],
)
def get_event_certificates(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CertificateService.get_event_certificates(
        db=db,
        event_id=event_id,
        current_user=current_user,
    )