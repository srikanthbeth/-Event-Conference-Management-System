from sqlalchemy.orm import Session

from models.audit_log import AuditLog


class AuditLogRepository:

    @staticmethod
    def create(
        db: Session,
        audit_log: AuditLog,
    ) -> AuditLog:
        db.add(audit_log)
        db.flush()
        return audit_log

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AuditLog]:
        return (
            db.query(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )