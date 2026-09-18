from datetime import datetime

from sqlalchemy.orm import Session

from models.payment import Payment


class PaymentRepository:

    @staticmethod
    def create(
        db: Session,
        payment: Payment,
    ) -> Payment:

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    @staticmethod
    def get_by_id(
        db: Session,
        payment_id: int,
    ) -> Payment | None:

        return (
            db.query(Payment)
            .filter(
                Payment.id == payment_id
            )
            .first()
        )

    @staticmethod
    def get_by_transaction_id(
        db: Session,
        transaction_id: str,
    ) -> Payment | None:

        return (
            db.query(Payment)
            .filter(
                Payment.transaction_id
                == transaction_id
            )
            .first()
        )

    @staticmethod
    def get_by_purchase_id(
        db: Session,
        purchase_id: int,
    ) -> Payment | None:

        return (
            db.query(Payment)
            .filter(
                Payment.purchase_id
                == purchase_id
            )
            .first()
        )

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        payment_status=None,
        payment_method=None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sort_by: str = "payment_date",
        sort_order: str = "desc",
    ) -> list[Payment]:

        query = db.query(Payment)

        # ---------------------------------------------------------
        # Filters
        # ---------------------------------------------------------

        if payment_status is not None:
            query = query.filter(
                Payment.payment_status
                == payment_status
            )

        if payment_method is not None:
            query = query.filter(
                Payment.payment_method
                == payment_method
            )

        if start_date is not None:
            query = query.filter(
                Payment.payment_date >= start_date
            )

        if end_date is not None:
            query = query.filter(
                Payment.payment_date <= end_date
            )

        # ---------------------------------------------------------
        # Sorting
        # ---------------------------------------------------------

        sort_columns = {
            "id": Payment.id,
            "purchase_id": Payment.purchase_id,
            "transaction_id": Payment.transaction_id,
            "payment_method": Payment.payment_method,
            "amount": Payment.amount,
            "payment_status": Payment.payment_status,
            "payment_date": Payment.payment_date,
        }

        sort_column = sort_columns.get(
            sort_by,
            Payment.payment_date,
        )

        if sort_order.lower() == "asc":
            query = query.order_by(
                sort_column.asc()
            )
        else:
            query = query.order_by(
                sort_column.desc()
            )

        return (
            query
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def update(
        db: Session,
        payment: Payment,
    ) -> Payment:

        db.commit()
        db.refresh(payment)

        return payment