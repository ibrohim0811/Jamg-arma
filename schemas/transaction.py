import uuid
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class TransactionResponse(BaseModel):
    id: uuid.UUID
    sender_card_id: uuid.UUID | None
    receiver_card_id: uuid.UUID | None
    amount: Decimal
    currency: str
    status: str
    transaction_type: str
    service_type: str | None = None
    provider: str | None = None
    recipient_phone: str | None = None
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True