from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.event import Event
from models.payment import Payment
from models.purchase import Purchase
from models.registration import Registration
from models.refund import Refund
from models.user import User

from repositories.refund_repository import RefundRepository

from utils.enums import (
    EventStatus,
    PaymentStatus,
    RegistrationStatus,
    RefundStatus,
    UserRole,
)


class RefundService:

    PARTIAL_REFUND_HOURS = 48

    @staticmethod
    def _check_attendee_owns_purchase(
        purchase: Purchase,
        current_user: User,
    ) -> None:

        if current_user.role != UserRole.ATTENDEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only attendees can cancel their purchases",
            )

        if purchase.registration.attendee.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own purchase",
            )

    @staticmethod
    def _calculate_refund_amount(
        purchase: Purchase,
        event: Event,
    ) -> Decimal:

        now = datetime.utcnow()

        if now >= event.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancellation is not allowed after the event has started",
            )

        hours_until_event = (
            event.start_date - now
        ).total_seconds() / 3600

        total_amount = Decimal(str(purchase.total_amount))

        if hours_until_event <= RefundService.PARTIAL_REFUND_HOURS:
            return (total_amount * Decimal("0.50")).quantize(
                Decimal("0.01")
            )

        return total_amount.quantize(Decimal("0.01"))

    @staticmethod
    def cancel_purchase(
        db: Session,
        purchase_id: int,
        reason: str,
        current_user: User,
    ):

        purchase = (
            db.query(Purchase)
            .filter(Purchase.id == purchase_id)
            .first()
        )

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found",
            )

        RefundService._check_attendee_owns_purchase(
            purchase,
            current_user,
        )

        existing_refund = RefundRepository.get_by_purchase_id(
            db,
            purchase_id,
        )

        if existing_refund:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase has already been cancelled",
            )

        payment = (
            db.query(Payment)
            .filter(Payment.purchase_id == purchase_id)
            .first()
        )

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase does not have a payment",
            )

        if payment.payment_status != PaymentStatus.SUCCESSFUL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only successful payments can be refunded",
            )

        event = (
            db.query(Event)
            .filter(
                Event.id == purchase.registration.event_id
            )
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        if event.status == EventStatus.CANCELLED:
            refund_amount = Decimal(
                str(purchase.total_amount)
            ).quantize(Decimal("0.01"))
        else:
            refund_amount = RefundService._calculate_refund_amount(
                purchase,
                event,
            )

        purchase.registration.registration_status = (
            RegistrationStatus.CANCELLED
        )

        refund = Refund(
            payment_id=payment.id,
            purchase_id=purchase.id,
            cancellation_reason=reason,
            refund_amount=refund_amount,
            refund_status=RefundStatus.PENDING,
        )

        db.add(refund)
        db.commit()
        db.refresh(refund)

        return refund

    @staticmethod
    def cancel_event(
        db: Session,
        event_id: int,
        reason: str,
        current_user: User,
    ):

        event = (
            db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        if current_user.role not in (
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and event organizers can cancel events",
            )

        if (
            current_user.role == UserRole.EVENT_ORGANIZER
            and event.organizer_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own events",
            )

        if event.status == EventStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is already cancelled",
            )

        event.status = EventStatus.CANCELLED

        purchases = (
            db.query(Purchase)
            .join(
                Registration,
                Purchase.registration_id == Registration.id,
            )
            .filter(
                Registration.event_id == event_id
            )
            .all()
        )

        created_refunds = []

        for purchase in purchases:

            payment = (
                db.query(Payment)
                .filter(
                    Payment.purchase_id == purchase.id
                )
                .first()
            )

            if not payment:
                continue

            if payment.payment_status != PaymentStatus.SUCCESSFUL:
                continue

            existing_refund = (
                RefundRepository.get_by_purchase_id(
                    db,
                    purchase.id,
                )
            )

            if existing_refund:
                continue

            purchase.registration.registration_status = (
                RegistrationStatus.CANCELLED
            )

            refund = Refund(
                payment_id=payment.id,
                purchase_id=purchase.id,
                cancellation_reason=reason,
                refund_amount=Decimal(
                    str(purchase.total_amount)
                ).quantize(Decimal("0.01")),
                refund_status=RefundStatus.PENDING,
            )

            db.add(refund)
            created_refunds.append(refund)

        db.commit()

        for refund in created_refunds:
            db.refresh(refund)

        return {
            "event_id": event.id,
            "event_name": event.event_name,
            "event_status": event.status,
            "cancellation_reason": reason,
            "refunds_created": len(created_refunds),
            "refunds": created_refunds,
        }

    @staticmethod
    def get_refund(
        db: Session,
        refund_id: int,
        current_user: User,
    ):

        refund = RefundRepository.get_by_id(
            db,
            refund_id,
        )

        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found",
            )

        purchase = (
            db.query(Purchase)
            .filter(Purchase.id == refund.purchase_id)
            .first()
        )

        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found",
            )

        if current_user.role == UserRole.ADMIN:
            return refund

        if current_user.role == UserRole.EVENT_ORGANIZER:

            event = (
                db.query(Event)
                .filter(
                    Event.id
                    == purchase.registration.event_id
                )
                .first()
            )

            if event and event.organizer_id == current_user.id:
                return refund

        if (
            current_user.role == UserRole.ATTENDEE
            and purchase.registration.attendee.email
            == current_user.email
        ):
            return refund

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this refund",
        )

    @staticmethod
    def get_purchase_refund(
        db: Session,
        purchase_id: int,
        current_user: User,
    ):

        refund = RefundRepository.get_by_purchase_id(
            db,
            purchase_id,
        )

        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found for this purchase",
            )

        return RefundService.get_refund(
            db,
            refund.id,
            current_user,
        )

    @staticmethod
    def complete_refund(
        db: Session,
        refund_id: int,
        current_user: User,
    ):

        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can complete refunds",
            )

        refund = RefundRepository.get_by_id(
            db,
            refund_id,
        )

        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found",
            )

        if refund.refund_status == RefundStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refund is already completed",
            )

        return RefundRepository.update_status(
            db,
            refund,
            RefundStatus.COMPLETED,
        )