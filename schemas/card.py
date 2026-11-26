import uuid
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime

class CardCreate(BaseModel):
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)

class CardResponse(BaseModel):
    id: uuid.UUID
    card_number: int
    balance: Decimal
    is_frozen: bool
    created_at: datetime
    user_fullname: str

    class Config:
        from_attributes = True  # SQLAlchemy modellarini avtomatik Pydantic modeliga o'tkazish uchun


class GetCardNumberSchema(BaseModel):
    card_number: int



class CardFoundResponse(BaseModel):
    card_number: int
    is_frozen: bool
    user_fullname: Optional[str] = None

    class Config:
        from_attributes = True



class CardTopUpRequest(BaseModel):
    card_id: str
    amount: Decimal = Field(..., gt=Decimal("0.00"), max_digits=15, decimal_places=2)
    description: str | None = Field(default="Kartani to'ldirish", max_length=255)


class CardTopUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: uuid.UUID
    card_id: uuid.UUID
    amount: Decimal
    new_balance: Decimal
    status: str
    transaction_type: str
    created_at: datetime