from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from schemas.p2p import P2PTransferCreate
from crud import p2p as p2p_crud

from services.push_service import send_expo_push

router = APIRouter(prefix="/p2p", tags=["P2P Transfers"])

@router.post("/transfer", status_code=status.HTTP_201_CREATED)
async def p2p_transfer(
    transfer_in: P2PTransferCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Kartadan kartaga pul o'tkazish (P2P)
    """
    transaction, receiver_user_id = await p2p_crud.make_p2p_transfer(
        db=db, transfer_in=transfer_in, user_id=current_user.id
    )

    sender_name = f"{current_user.first_name} {current_user.last_name}".strip()
    background_tasks.add_task(
        send_expo_push,
        db=db,
        user_id=receiver_user_id,
        title="Hisobingiz to'ldirildi 💸",
        body=f"+{transfer_in.amount:,.0f} UZS • {sender_name} dan",
        data={"type": "p2p_received", "transaction_id": str(transaction.id)}
    )

    return {
        "message": "O'tkazma muvaffaqiyatli amalga oshirildi",
        "transaction_id": transaction.id,
        "amount": transaction.amount
    }