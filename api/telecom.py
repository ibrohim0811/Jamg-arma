from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from schemas.telecom import TelecomPaymentCreate
from crud import telecom as telecom_crud

router = APIRouter(prefix="/telecom", tags=["Telecom Payments"])

@router.post("/pay", status_code=status.HTTP_201_CREATED)
async def make_telecom_payment(
    payment_in: TelecomPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Mobil aloqa yoki internet provayderiga to'lov qilish
    """
    transaction = await telecom_crud.pay_telecom_service(db=db, payment_in=payment_in, user_id=current_user.id)
    return {"message": "To'lov muvaffaqiyatli amalga oshirildi", "transaction_id": transaction.id}