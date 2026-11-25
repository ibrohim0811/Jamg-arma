from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from decimal import Decimal

from models.users import CreditCard, Transaction, TransactionType
from schemas.p2p import P2PTransferCreate
from crud.card import get_user_card_by_identifier

async def make_p2p_transfer(db: AsyncSession, transfer_in: P2PTransferCreate, user_id: int) -> Transaction:
    # 1. Yuboruvchi kartasini tekshirish
    sender_card = await get_user_card_by_identifier(
        db=db,
        user_id=user_id,
        card_identifier=transfer_in.sender_card_id,
        for_update=True,
    )
    if not sender_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Yuboruvchi kartasi topilmadi")
    
    if sender_card.is_frozen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sizning kartangiz muzlatilgan")
    
    if sender_card.card_number == transfer_in.receiver_card_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O'z kartangizga pul o'tkaza olmaysiz")

    if sender_card.balance < transfer_in.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kartada mablag' yetarli emas")

    # 2. Qabul qiluvchi kartasini topish
    receiver_card_result = await db.execute(
        select(CreditCard).filter(CreditCard.card_number == transfer_in.receiver_card_number)
    )
    receiver_card = receiver_card_result.scalars().first()
    if not receiver_card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Qabul qiluvchi karta raqami topilmadi")
    
    if receiver_card.is_frozen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Qabul qiluvchi karta muzlatilgan")

    # 3. Balanslarni o'zgartirish
    sender_card.balance -= transfer_in.amount
    receiver_card.balance += transfer_in.amount

    # 4. Tranzaksiya yaratish
    db_transaction = Transaction(
        sender_card_id=sender_card.id,
        receiver_card_id=receiver_card.id,
        amount=transfer_in.amount,
        currency="UZS",
        status="success",
        transaction_type=TransactionType.P2P,
        description=transfer_in.description or "P2P o'tkazma"
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)

    return db_transaction