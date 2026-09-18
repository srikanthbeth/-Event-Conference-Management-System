from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketUpdate,
)
from services.ticket_service import TicketService
from utils.dependencies import get_current_user


router = APIRouter(
    tags=["Tickets"],
)


@router.post(
    "/events/{event_id}/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    event_id: int,
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TicketService.create_ticket(
        db=db,
        event_id=event_id,
        payload=payload,
        current_user=current_user,
    )


@router.get(
    "/events/{event_id}/tickets",
    response_model=list[TicketResponse],
)
def get_event_tickets(
    event_id: int,
    db: Session = Depends(get_db),
):
    return TicketService.get_event_tickets(
        db=db,
        event_id=event_id,
    )


@router.put(
    "/tickets/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TicketService.update_ticket(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        current_user=current_user,
    )