from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.purchase import PurchaseCreate, PurchaseResponse
from services.purchase_service import PurchaseService
from utils.dependencies import get_current_user


router = APIRouter(
    tags=["Purchases"],
)


@router.post(
    "/tickets/{ticket_id}/purchase",
    response_model=PurchaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def purchase_ticket(
    ticket_id: int,
    payload: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PurchaseService.create_purchase(
        db=db,
        ticket_id=ticket_id,
        payload=payload,
        current_user=current_user,
    )


@router.get(
    "/purchases/{purchase_id}",
    response_model=PurchaseResponse,
)
def get_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PurchaseService.get_purchase(
        db=db,
        purchase_id=purchase_id,
        current_user=current_user,
    )