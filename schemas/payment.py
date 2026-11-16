from pydantic import BaseModel, Field
from decimal import Decimal
import uuid
from datetime import datetime
from models.users import CommunalTypes
# CommunalTypes ni o'zingizning enum joylashgan fayldan import qilasiz

class CommunalPaymentCreate(BaseModel):
    card_id: uuid.UUID
    service_type: CommunalTypes
    provider_name: str = Field(..., max_length=150)
    account_number: str = Field(..., max_length=50)
    amount: Decimal = Field(..., gt=0)  # Summa 0 dan katta bo'lishi shart

class CommunalPaymentResponse(BaseModel):
    id: uuid.UUID
    user_id: int
    card_id: uuid.UUID | None
    transaction_id: uuid.UUID | None
    service_type: CommunalTypes
    provider_name: str
    account_number: str
    amount: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True