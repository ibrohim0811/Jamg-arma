from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db
from core.deps import get_current_user
from schemas.transaction import TransactionResponse
from crud import transaction as transaction_crud

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/", response_model=List[TransactionResponse])
async def get_my_transactions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Foydalanuvchining barcha tranzaksiyalari tarixi (P2P, Kommunal, Telecom...)
    """
    return await transaction_crud.get_user_transactions(db=db, user_id=current_user.id)