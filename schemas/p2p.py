from pydantic import BaseModel, Field
from decimal import Decimal
import uuid

class P2PTransferCreate(BaseModel):
    sender_card_id: str
    receiver_card_number: int  # Qabul qiluvchining 16 xonali karta raqami
    amount: Decimal = Field(..., gt=0)
    description: str | None = Field(None, max_length=255)