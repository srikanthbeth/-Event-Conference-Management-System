from sqlalchemy.orm import Session

from models.ticket import Ticket
from utils.enums import TicketType


class TicketRepository:

    @staticmethod
    def create(db: Session, ticket: Ticket) -> Ticket:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    @staticmethod
    def get_by_id(db: Session, ticket_id: int) -> Ticket | None:
        return (
            db.query(Ticket)
            .filter(Ticket.id == ticket_id)
            .first()
        )

    @staticmethod
    def get_by_event(
        db: Session,
        event_id: int,
    ) -> list[Ticket]:
        return (
            db.query(Ticket)
            .filter(Ticket.event_id == event_id)
            .order_by(Ticket.id)
            .all()
        )

    @staticmethod
    def get_by_event_and_type(
        db: Session,
        event_id: int,
        ticket_type: TicketType,
    ) -> Ticket | None:
        return (
            db.query(Ticket)
            .filter(
                Ticket.event_id == event_id,
                Ticket.ticket_type == ticket_type,
            )
            .first()
        )

    @staticmethod
    def update(
        db: Session,
        ticket: Ticket,
    ) -> Ticket:
        db.commit()
        db.refresh(ticket)
        return ticket