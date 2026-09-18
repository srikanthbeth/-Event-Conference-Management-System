from datetime import datetime

from pydantic import BaseModel, ConfigDict

from utils.enums import CertificateStatus, CertificateType


class CertificateCreate(BaseModel):
    certificate_type: CertificateType = CertificateType.PARTICIPATION


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    certificate_number: str
    registration_id: int
    event_id: int
    attendee_id: int
    issue_date: datetime
    certificate_type: CertificateType
    status: CertificateStatus