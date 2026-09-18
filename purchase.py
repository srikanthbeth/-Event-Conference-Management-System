from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PurchaseCreate(BaseModel):
    registration_id: int
    quantity: int = Field(..., gt=0)
    discount: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )
    tax: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
    )


class PurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    registration_id: int
    ticket_id: int
    quantity: int
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime