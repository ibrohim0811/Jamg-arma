from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from schemas.p2p import P2PTransferCreate
from crud import p2p as p2p_crud

router = APIRouter(prefix="/p2p", tags=["P2P Transfers"])

@router.post("/transfer", status_code=status.HTTP_201_CREATED)
async def p2p_transfer(
    transfer_in: P2PTransferCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Kartadan kartaga pul o'tkazish (P2P)
    """
    transaction = await p2p_crud.make_p2p_transfer(db=db, transfer_in=transfer_in, user_id=current_user.id)
    return {
        "message": "O'tkazma muvaffaqiyatli amalga oshirildi",
        "transaction_id": transaction.id,
        "amount": transaction.amount
    }