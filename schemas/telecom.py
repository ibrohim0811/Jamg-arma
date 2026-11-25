from pydantic import BaseModel, Field
from decimal import Decimal
# Communal model faylingizdagi TelecomProvider enum'ini import qilasiz
from models.users import TelecomProvider 

class TelecomPaymentCreate(BaseModel):
    card_id: str
    provider: TelecomProvider
    recipient_phone: str = Field(..., max_length=20)  # Masalan: "+998901234567"
    amount: Decimal = Field(..., gt=0)