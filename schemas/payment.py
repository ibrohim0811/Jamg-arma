from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
import uuid

class CommunalTransactionCreate(BaseModel):
    sender_card_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    service_type: str  # "electricity", "gas", "water", va hokazo.
    description: Optional[str] = None