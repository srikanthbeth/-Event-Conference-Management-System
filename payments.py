from datetime import datetime

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Query,
    status,
)

from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.payment import (
    PaymentCreate,
    PaymentResponse,
)
from services.payment_service import PaymentService
from utils.dependencies import get_current_user
from utils.enums import (
    PaymentMethod,
    PaymentStatus,
)


router = APIRouter(
    tags=["Payments"],
)


@router.post(
    "/payments/{purchase_id}",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment(
    purchase_id: int,
    payload: PaymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PaymentService.create_payment(
        db=db,
        purchase_id=purchase_id,
        payload=payload,
        current_user=current_user,
        background_tasks=background_tasks,
    )


@router.get(
    "/payments",
    response_model=list[PaymentResponse],
)
def list_payments(
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        100,
        ge=1,
        le=100,
    ),
    payment_status: PaymentStatus | None = Query(
        None,
    ),
    payment_method: PaymentMethod | None = Query(
        None,
    ),
    start_date: datetime | None = Query(
        None,
        description="Payment date from",
    ),
    end_date: datetime | None = Query(
        None,
        description="Payment date until",
    ),
    sort_by: str = Query(
        "payment_date",
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit

    allowed_sort_fields = {
        "id",
        "purchase_id",
        "transaction_id",
        "payment_method",
        "amount",
        "payment_status",
        "payment_date",
    }

    if sort_by not in allowed_sort_fields:
        sort_by = "payment_date"

    return PaymentService.list_payments(
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


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PaymentService.get_payment(
        db=db,
        payment_id=payment_id,
        current_user=current_user,
    )