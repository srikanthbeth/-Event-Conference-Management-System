from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.refund import (
    CancellationCreate,
    EventCancellationCreate,
    RefundResponse,
)
from services.refund_service import RefundService
from utils.dependencies import get_current_user


router = APIRouter(
    tags=["Cancellation & Refund"],
)


@router.post(
    "/purchases/{purchase_id}/cancel",
    response_model=RefundResponse,
    status_code=status.HTTP_201_CREATED,
)
def cancel_purchase(
    purchase_id: int,
    payload: CancellationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RefundService.cancel_purchase(
        db=db,
        purchase_id=purchase_id,
        reason=payload.reason,
        current_user=current_user,
    )


@router.post(
    "/events/{event_id}/cancel",
)
def cancel_event(
    event_id: int,
    payload: EventCancellationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RefundService.cancel_event(
        db=db,
        event_id=event_id,
        reason=payload.reason,
        current_user=current_user,
    )


@router.get(
    "/refunds/{refund_id}",
    response_model=RefundResponse,
)
def get_refund(
    refund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RefundService.get_refund(
        db=db,
        refund_id=refund_id,
        current_user=current_user,
    )


@router.get(
    "/purchases/{purchase_id}/refund",
    response_model=RefundResponse,
)
def get_purchase_refund(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RefundService.get_purchase_refund(
        db=db,
        purchase_id=purchase_id,
        current_user=current_user,
    )


@router.patch(
    "/refunds/{refund_id}/complete",
    response_model=RefundResponse,
)
def complete_refund(
    refund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return RefundService.complete_refund(
        db=db,
        refund_id=refund_id,
        current_user=current_user,
    )