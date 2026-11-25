from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from decimal import Decimal

from models.users import CreditCard, Transaction, TransactionType, TelecomProvider
from schemas.telecom import TelecomPaymentCreate
from crud.card import get_user_card_by_identifier

async def pay_telecom_service(db: AsyncSession, payment_in: TelecomPaymentCreate, user_id: int) -> Transaction:
    # 1. Kartani tekshirish
    card = await get_user_card_by_identifier(
        db=db,
        user_id=user_id,
        card_identifier=payment_in.card_id,
        for_update=True,
    )
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Karta topilmadi")
    
    if card.is_frozen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Karta muzlatilgan")
    
    if card.balance < payment_in.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kartada mablag' yetarli emas")

    # 2. Balansdan pulni yechish
    card.balance -= payment_in.amount

    # 3. Tranzaksiya yaratish
    db_transaction = Transaction(
        sender_card_id=card.id,
        receiver_card_id=None,
        amount=payment_in.amount,
        currency="UZS",
        status="success",
        transaction_type=TransactionType.TELECOM,
        provider=payment_in.provider.value,
        recipient_phone=payment_in.recipient_phone,
        description=f"{payment_in.provider.value.upper()} mobil aloqa/internet to'lovi: {payment_in.recipient_phone}"
    )
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    
    return db_transaction