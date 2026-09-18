from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.registration import Registration
from models.ticket import Ticket
from models.user import User
from models.purchase import Purchase
from repositories.purchase_repository import PurchaseRepository
from schemas.purchase import PurchaseCreate
from services.ticket_service import TicketService
from utils.enums import RegistrationStatus, UserRole


class PurchaseService:

    @staticmethod
    def create_purchase(
        db: Session,
        ticket_id: int,
        payload: PurchaseCreate,
        current_user: User,
    ):

        if current_user.role != UserRole.ATTENDEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only attendees can purchase tickets",
            )

        ticket = (
            db.query(Ticket)
            .filter(Ticket.id == ticket_id)
            .first()
        )

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        registration = (
            db.query(Registration)
            .filter(
                Registration.id == payload.registration_id
            )
            .first()
        )

        if not registration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )

        if registration.attendee.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only purchase for your own registration",
            )

        if registration.registration_status == RegistrationStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cancelled registration cannot purchase tickets",
            )

        if registration.event_id != ticket.event_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Ticket does not belong to the registered event"
                ),
            )

        if not TicketService.is_ticket_on_sale(ticket):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket is not currently available for purchase",
            )

        if payload.quantity > ticket.available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough tickets available",
            )

        subtotal = ticket.price * payload.quantity

        if payload.discount > subtotal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discount cannot exceed subtotal",
            )

        total_amount = (
            subtotal
            - payload.discount
            + payload.tax
        )

        if total_amount < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Total amount cannot be negative",
            )

        purchase = PurchaseRepository.get_by_registration_and_ticket(
            db,
            registration.id,
            ticket.id,
        )

        if purchase:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase already exists for this registration and ticket",
            )

        purchase = Purchase(
            registration_id=registration.id,
            ticket_id=ticket.id,
            quantity=payload.quantity,
            subtotal=subtotal,
            discount=payload.discount,
            tax=payload.tax,
            total_amount=total_amount,
        )

        # Reserve/deduct ticket quantity immediately.
        ticket.available_quantity -= payload.quantity

        db.add(ticket)

        return PurchaseRepository.create(db, purchase)

    @staticmethod
    def get_purchase(
        db: Session,
        purchase_id: int,
        current_user: User,
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

        if current_user.role == UserRole.ADMIN:
            return purchase

        if (
            current_user.role != UserRole.ATTENDEE
            or purchase.registration.attendee.email
            != current_user.email
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot access this purchase",
            )

        return purchase