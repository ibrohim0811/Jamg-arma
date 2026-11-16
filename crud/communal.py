from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
import uuid

from models.users import Transaction, CreditCard, TransactionType
from schemas.payment import CommunalTransactionCreate

async def create_communal_payment(db: AsyncSession, payment_data: CommunalTransactionCreate) -> Transaction:
    """
    Kommunal to'lov uchun tranzaksiya yaratish va balansdan pul yechish.
    """
    # 1. Yechib olinadigan kartani topamiz
    result = await db.execute(
        select(CreditCard).where(CreditCard.id == payment_data.sender_card_id)
    )
    sender_card = result.scalars().first()
    
    if not sender_card:
        raise ValueError("Karta topilmadi!")
    
    if sender_card.is_frozen:
        raise ValueError("Karta muzlatilgan!")
        
    if sender_card.balance < payment_data.amount:
        raise ValueError("Kartada yetarli mablag' mavjud emas!")

    # 2. Balansdan pulni ayiramiz
    sender_card.balance -= payment_data.amount

    # 3. Tranzaksiya obyektini yaratamiz
    new_transaction = Transaction(
        id=uuid.uuid4(),
        sender_card_id=payment_data.sender_card_id,
        receiver_card_id=None,  # Kommunal uchun qabul qiluvchi karta yo'q
        amount=payment_data.amount,
        currency="UZS",
        status="success",  # To'g'ridan-to'g'ri muvaffaqiyatli deb olamiz yoki pending
        transaction_type=TransactionType.COMMUNAL,
        service_type=payment_data.service_type,
        description=payment_data.description or f"Kommunal to'lov: {payment_data.service_type}"
    )

    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    
    return new_transaction


async def get_user_communal_transactions(db: AsyncSession, card_ids: list[uuid.UUID], skip: int = 0, limit: int = 10) -> list[Transaction]:
    """
    Foydalanuvchi kartalariga tegishli barcha kommunal to'lovlar tarixini olish.
    """
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.transaction_type == TransactionType.COMMUNAL,
            Transaction.sender_card_id.in_(card_ids)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_transaction_by_id(db: AsyncSession, transaction_id: uuid.UUID) -> Transaction | None:
    """
    ID bo'yicha tranzaksiyani topish.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    return result.scalars().first()