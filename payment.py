from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1)
    payment_method: PaymentMethod
    amount: Decimal = Field(..., ge=0)
    payment_status: PaymentStatus


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    purchase_id: int
    transaction_id: str
    payment_method: PaymentMethod
    amount: Decimal
    payment_status: PaymentStatus
    payment_date: datetime