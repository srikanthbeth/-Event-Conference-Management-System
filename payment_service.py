from datetime import datetime

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from models.event import Event
from models.payment import Payment
from models.user import User

from repositories.payment_repository import PaymentRepository
from repositories.purchase_repository import PurchaseRepository

from schemas.payment import PaymentCreate

from services.notification_tasks import (
    send_payment_success,
    send_registration_confirmation,
    send_ticket_confirmation,
)

from utils.enums import (
    PaymentStatus,
    RegistrationStatus,
    UserRole,
)


class PaymentService:

    @staticmethod
    def create_payment(
        db: Session,
        purchase_id: int,
        payload: PaymentCreate,
        current_user: User,
        background_tasks: BackgroundTasks | None = None,
    ):

        purchase = PurchaseRepository.get_by_id(
            db,
            purchase_id,
        )

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found",
            )

        if current_user.role == UserRole.ATTENDEE:

            if (
                purchase.registration.attendee.email
                != current_user.email
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot pay for this purchase",
                )

        elif current_user.role != UserRole.ADMIN:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not allowed to make this payment",
            )

        existing_transaction = (
            PaymentRepository.get_by_transaction_id(
                db,
                payload.transaction_id,
            )
        )

        if existing_transaction:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate transaction ID",
            )

        existing_payment = (
            PaymentRepository.get_by_purchase_id(
                db,
                purchase_id,
            )
        )

        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already exists for this purchase",
            )

        if payload.amount != purchase.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must match purchase amount",
            )

        payment = Payment(
            purchase_id=purchase_id,
            transaction_id=payload.transaction_id,
            payment_method=payload.payment_method,
            amount=payload.amount,
            payment_status=payload.payment_status,
        )

        payment = PaymentRepository.create(
            db,
            payment,
        )

        if payload.payment_status == PaymentStatus.SUCCESSFUL:

            purchase.registration.registration_status = (
                RegistrationStatus.CONFIRMED
            )

            db.commit()
            db.refresh(payment)

            if background_tasks is not None:

                event = db.query(Event).filter(
                    Event.id
                    == purchase.registration.event_id
                ).first()

                if event:

                    event_name = event.event_name

                    background_tasks.add_task(
                        send_payment_success,
                        current_user.id,
                        event_name,
                    )

                    background_tasks.add_task(
                        send_registration_confirmation,
                        current_user.id,
                        event_name,
                    )

                    background_tasks.add_task(
                        send_ticket_confirmation,
                        current_user.id,
                        event_name,
                    )

        elif payload.payment_status == PaymentStatus.FAILED:

            db.commit()
            db.refresh(payment)

        return payment

    @staticmethod
    def get_payment(
        db: Session,
        payment_id: int,
        current_user: User,
    ):

        payment = PaymentRepository.get_by_id(
            db,
            payment_id,
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found",
            )

        if current_user.role == UserRole.ADMIN:
            return payment

        if (
            current_user.role != UserRole.ATTENDEE
            or payment.purchase.registration.attendee.email
            != current_user.email
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this payment",
            )

        return payment

    @staticmethod
    def list_payments(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        payment_status=None,
        payment_method=None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sort_by: str = "payment_date",
        sort_order: str = "desc",
    ):
        return PaymentRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            payment_status=payment_status,
            payment_method=payment_method,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )