from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.deps import get_current_user
from schemas.payment import CommunalPaymentCreate, CommunalPaymentResponse
from crud import communal as communal_crud

router = APIRouter(prefix="/communal", tags=["Communal Payments"])

@router.post("/pay", response_model=CommunalPaymentResponse, status_code=status.HTTP_201_CREATED)
async def make_communal_payment(
    payment_in: CommunalPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)  # Token orqali kelgan foydalanuvchi
):
    """
    Kommunal to'lovni amalga oshirish (Karta balansidan pul yechiladi va tranzaksiya yoziladi)
    """
    return await communal_crud.pay_communal_service(db=db, payment_in=payment_in, user_id=current_user.id)

@router.get("/history", response_model=List[CommunalPaymentResponse])
async def communal_history(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Foydalanuvchining barcha kommunal to'lovlar tarixi
    """
    return await communal_crud.get_user_communal_history(db=db, user_id=current_user.id)