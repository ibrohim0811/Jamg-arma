from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

class TransactionResponse(BaseModel):
    id: str
    sender_card_id: str | None
    receiver_card_id: str | None
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