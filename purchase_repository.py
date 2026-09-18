from sqlalchemy.orm import Session

from models.purchase import Purchase


class PurchaseRepository:

    @staticmethod
    def create(
        db: Session,
        purchase: Purchase,
    ) -> Purchase:
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        return purchase

    @staticmethod
    def get_by_id(
        db: Session,
        purchase_id: int,
    ) -> Purchase | None:
        return (
            db.query(Purchase)
            .filter(Purchase.id == purchase_id)
            .first()
        )

    @staticmethod
    def get_by_registration_and_ticket(
        db: Session,
        registration_id: int,
        ticket_id: int,
    ) -> Purchase | None:
        return (
            db.query(Purchase)
            .filter(
                Purchase.registration_id == registration_id,
                Purchase.ticket_id == ticket_id,
            )
            .first()
        )