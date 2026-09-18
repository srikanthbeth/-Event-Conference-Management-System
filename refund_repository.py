from datetime import datetime

from sqlalchemy.orm import Session

from models.refund import Refund
from utils.enums import RefundStatus


class RefundRepository:

    @staticmethod
    def create(db: Session, refund: Refund) -> Refund:
        db.add(refund)
        db.commit()
        db.refresh(refund)
        return refund

    @staticmethod
    def get_by_id(
        db: Session,
        refund_id: int,
    ) -> Refund | None:
        return (
            db.query(Refund)
            .filter(Refund.id == refund_id)
            .first()
        )

    @staticmethod
    def get_by_purchase_id(
        db: Session,
        purchase_id: int,
    ) -> Refund | None:
        return (
            db.query(Refund)
            .filter(Refund.purchase_id == purchase_id)
            .first()
        )

    @staticmethod
    def get_by_payment_id(
        db: Session,
        payment_id: int,
    ) -> Refund | None:
        return (
            db.query(Refund)
            .filter(Refund.payment_id == payment_id)
            .first()
        )

    @staticmethod
    def get_all(db: Session) -> list[Refund]:
        return (
            db.query(Refund)
            .order_by(Refund.id.desc())
            .all()
        )

    @staticmethod
    def update_status(
        db: Session,
        refund: Refund,
        refund_status: RefundStatus,
    ) -> Refund:

        refund.refund_status = refund_status

        if refund_status == RefundStatus.COMPLETED:
            refund.refund_date = datetime.utcnow()

        db.commit()
        db.refresh(refund)

        return refund