from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.event import Event
from models.ticket import Ticket
from models.user import User
from repositories.ticket_repository import TicketRepository
from schemas.ticket import TicketCreate, TicketUpdate
from utils.enums import TicketType, UserRole


class TicketService:

    @staticmethod
    def _check_management_permission(user: User) -> None:
        if user.role not in {
            UserRole.ADMIN,
            UserRole.EVENT_ORGANIZER,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin or Event Organizer can manage tickets",
            )

    @staticmethod
    def _validate_ticket_values(
        quantity: int,
        available_quantity: int,
        sale_start: datetime,
        sale_end: datetime,
    ) -> None:

        if quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket quantity cannot be negative",
            )

        if available_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Available quantity cannot be negative",
            )

        if available_quantity > quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Available quantity cannot exceed total ticket quantity"
                ),
            )

        if sale_end <= sale_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sale end must be after sale start",
            )

    @staticmethod
    def create_ticket(
        db: Session,
        event_id: int,
        payload: TicketCreate,
        current_user: User,
    ) -> Ticket:

        TicketService._check_management_permission(current_user)

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

        if event.status.value == "Cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tickets cannot be created for a cancelled event",
            )

        # Event organizer can only manage their own event.
        if current_user.role == UserRole.EVENT_ORGANIZER:
            if event.organizer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only manage tickets for your own events",
                )

        TicketService._validate_ticket_values(
            quantity=payload.quantity,
            available_quantity=payload.available_quantity,
            sale_start=payload.sale_start,
            sale_end=payload.sale_end,
        )

        existing_ticket = TicketRepository.get_by_event_and_type(
            db,
            event_id,
            payload.ticket_type,
        )

        if existing_ticket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{payload.ticket_type.value} ticket category "
                    "already exists for this event"
                ),
            )

        ticket = Ticket(
            event_id=event_id,
            ticket_type=payload.ticket_type,
            price=payload.price,
            quantity=payload.quantity,
            available_quantity=payload.available_quantity,
            sale_start=payload.sale_start,
            sale_end=payload.sale_end,
        )

        return TicketRepository.create(db, ticket)

    @staticmethod
    def get_event_tickets(
        db: Session,
        event_id: int,
    ) -> list[Ticket]:

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

        return TicketRepository.get_by_event(db, event_id)

    @staticmethod
    def update_ticket(
        db: Session,
        ticket_id: int,
        payload: TicketUpdate,
        current_user: User,
    ) -> Ticket:

        TicketService._check_management_permission(current_user)

        ticket = TicketRepository.get_by_id(db, ticket_id)

        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        event = (
            db.query(Event)
            .filter(Event.id == ticket.event_id)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        if current_user.role == UserRole.EVENT_ORGANIZER:
            if event.organizer_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only manage tickets for your own events",
                )

        new_ticket_type = (
            payload.ticket_type
            if payload.ticket_type is not None
            else ticket.ticket_type
        )

        new_price = (
            payload.price
            if payload.price is not None
            else ticket.price
        )

        new_quantity = (
            payload.quantity
            if payload.quantity is not None
            else ticket.quantity
        )

        new_available_quantity = (
            payload.available_quantity
            if payload.available_quantity is not None
            else ticket.available_quantity
        )

        new_sale_start = (
            payload.sale_start
            if payload.sale_start is not None
            else ticket.sale_start
        )

        new_sale_end = (
            payload.sale_end
            if payload.sale_end is not None
            else ticket.sale_end
        )

        if new_ticket_type != ticket.ticket_type:
            existing_ticket = TicketRepository.get_by_event_and_type(
                db,
                ticket.event_id,
                new_ticket_type,
            )

            if existing_ticket and existing_ticket.id != ticket.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"{new_ticket_type.value} ticket category "
                        "already exists for this event"
                    ),
                )

        TicketService._validate_ticket_values(
            quantity=new_quantity,
            available_quantity=new_available_quantity,
            sale_start=new_sale_start,
            sale_end=new_sale_end,
        )

        ticket.ticket_type = new_ticket_type
        ticket.price = new_price
        ticket.quantity = new_quantity
        ticket.available_quantity = new_available_quantity
        ticket.sale_start = new_sale_start
        ticket.sale_end = new_sale_end

        return TicketRepository.update(db, ticket)

    @staticmethod
    def is_ticket_on_sale(ticket: Ticket) -> bool:
        """
        Used by Level 8 Purchase & Payment.

        A ticket can only be purchased when:
        sale_start <= current time <= sale_end
        and available_quantity > 0.
        """
        now = datetime.utcnow()

        return (
            ticket.sale_start <= now <= ticket.sale_end
            and ticket.available_quantity > 0
        )