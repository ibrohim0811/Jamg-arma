from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from decimal import Decimal

from models.users import CommunalPayment, CreditCard, Transaction, TransactionType
from schemas.payment import CommunalPaymentCreate

async def pay_communal_service(db: AsyncSession, payment_in: CommunalPaymentCreate, user_id: int) -> CommunalPayment:
    # 1. Karta mavjudligini va foydalanuvchiga tegishliligini tekshirish
    card_result = await db.execute(
        select(CreditCard).filter(CreditCard.id == payment_in.card_id, CreditCard.user_id == user_id)
    )
    card = card_result.scalars().first()
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Karta topilmadi")
    
    if card.is_frozen:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Karta muzlatilgan")
    
    if card.balance < payment_in.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kartada mablag' yetarli emas")

    # 2. Balansdan pulni yechish
    card.balance -= payment_in.amount

    # 3. Tranzaksiya yaratish (Sizning Transaction modelingizga moslab)
    db_transaction = Transaction(
        sender_card_id=card.id,
        receiver_card_id=None,
        amount=payment_in.amount,
        currency="UZS",
        status="success",
        transaction_type=TransactionType.COMMUNAL,
        service_type=payment_in.service_type.value,
        description=f"{payment_in.provider_name} ga kommunal to'lov. Hisob raqam: {payment_in.account_number}"
    )
    db.add(db_transaction)
    await db.flush()  # Transaction ID hosil bo'lishi uchun flush qilamiz

    # 4. Communal payment tarixini saqlash
    db_communal = CommunalPayment(
        user_id=user_id,
        card_id=card.id,
        transaction_id=db_transaction.id,
        service_type=payment_in.service_type,
        provider_name=payment_in.provider_name,
        account_number=payment_in.account_number,
        amount=payment_in.amount,
        status="success"
    )
    db.add(db_communal)
    
    await db.commit()
    await db.refresh(db_communal)
    return db_communal



async def get_user_communal_history(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(CommunalPayment).filter(CommunalPayment.user_id == user_id).order_by(CommunalPayment.created_at.desc())
    )
    return result.scalars().all()