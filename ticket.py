from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from utils.enums import TicketType


class TicketCreate(BaseModel):
    ticket_type: TicketType
    price: Decimal = Field(..., ge=0)
    quantity: int = Field(..., ge=0)
    available_quantity: int = Field(..., ge=0)
    sale_start: datetime
    sale_end: datetime


class TicketUpdate(BaseModel):
    ticket_type: TicketType | None = None
    price: Decimal | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
    available_quantity: int | None = Field(default=None, ge=0)
    sale_start: datetime | None = None
    sale_end: datetime | None = None


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    ticket_type: TicketType
    price: Decimal
    quantity: int
    available_quantity: int
    sale_start: datetime
    sale_end: datetime
    created_at: datetime
    updated_at: datetime