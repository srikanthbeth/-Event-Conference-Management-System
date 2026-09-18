from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.audit_log import AuditLogResponse
from services.audit_log_service import AuditLogService
from utils.dependencies import get_current_user
from utils.enums import UserRole
from utils.exceptions import forbidden


router = APIRouter(
    prefix="/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise forbidden(
            "Only Admin can view audit logs"
        )

    return AuditLogService.list_logs(
        db=db,
        skip=skip,
        limit=limit,
    )