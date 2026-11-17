from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from models.users import Transaction, CreditCard

async def get_user_transactions(db: AsyncSession, user_id: int):
    # 1. Foydalanuvchiga tegishli barcha kartalar ID'larini topamiz
    cards_result = await db.execute(
        select(CreditCard.id).filter(CreditCard.user_id == user_id)
    )
    card_ids = [row[0] for row in cards_result.all()]
    
    if not card_ids:
        return []

    # 2. Shu kartalar qatnashgan barcha tranzaksiyalarni topamiz (yuborilgan yoki qabul qilingan)
    result = await db.execute(
        select(Transaction)
        .filter(
            or_(
                Transaction.sender_card_id.in_(card_ids),
                Transaction.receiver_card_id.in_(card_ids)
            )
        )
        .order_by(Transaction.created_at.desc())
    )
    return result.scalars().all()