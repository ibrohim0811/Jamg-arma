from pydantic import BaseModel, Field
from decimal import Decimal
import uuid
from datetime import datetime

class CardCreate(BaseModel):
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)

class CardResponse(BaseModel):
    card_number: int
    balance: Decimal
    is_frozen: bool
    created_at: datetime
    user_fullname: str

    class Config:
        from_attributes = True  # SQLAlchemy modellarini avtomatik Pydantic modeliga o'tkazish uchun


class GetCardNumberSchema(BaseModel):
    card_number: int