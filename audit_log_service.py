from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from repositories.audit_log_repository import AuditLogRepository


class AuditLogService:

    @staticmethod
    def log(
        db: Session,
        user_id: int | None,
        action: str,
        resource_type: str | None = None,
        resource_id: int | None = None,
        description: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
        )

        return AuditLogRepository.create(
            db,
            audit_log,
        )

    @staticmethod
    def list_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        return AuditLogRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
        )