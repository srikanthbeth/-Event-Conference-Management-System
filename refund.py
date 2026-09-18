from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import RefundStatus


class CancellationCreate(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class EventCancellationCreate(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_id: int
    purchase_id: int
    cancellation_reason: str
    refund_amount: Decimal
    refund_status: RefundStatus
    refund_date: datetime | None