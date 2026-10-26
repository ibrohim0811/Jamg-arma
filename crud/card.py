import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.users import CreditCard
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from models.users import CreditCard
from sqlalchemy.orm import selectinload

async def create_credit_card(
    db: AsyncSession, 
    user_id: int, 
    initial_balance: Decimal = Decimal("0.00")
) -> CreditCard:
    
    new_card = CreditCard(
        user_id=user_id,
        balance=initial_balance,
        is_frozen=False
    )
    
    db.add(new_card)
    
    await db.commit()
    
    await db.refresh(new_card)
    
    return new_card


async def get_my_card(db: AsyncSession, user_id: int):
    result = await db.execute(select(CreditCard).where(CreditCard.user_id == user_id))
    card = result.scalars().first()
    if card:
        return card
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sizda hali karta yaratilmagan !")



async def freeze_my_card(db: AsyncSession, user_id: int, card_number: int) -> CreditCard:
    stmt = select(CreditCard).where(
        CreditCard.user_id == user_id,
        CreditCard.card_number == card_number
    )
    result = await db.execute(stmt)
    card = result.scalars().first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bunday karta topilmadi yoki sizga tegishli emas."
        )

    if card.is_frozen:
        raise HTTPException(
            status_code=400,
            detail="Bu karta allaqachon muzlatilgan !"
        )
    
    card.is_frozen = True
    await db.commit()
    await db.refresh(card)
    
    return card


async def unfreeze_my_card(db: AsyncSession, user_id: int, card_number: int) -> CreditCard:
    stmt = select(CreditCard).where(
        CreditCard.user_id == user_id,
        CreditCard.card_number == card_number
    )
    result = await db.execute(stmt)
    card = result.scalars().first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bunday karta topilmadi yoki sizga tegishli emas."
        )

    if not card.is_frozen:
        raise HTTPException(
            status_code=400,
            detail="Bu karta muzlamagan !"
        )
    
    card.is_frozen = False
    await db.commit()
    await db.refresh(card)
    
    return card


def generate_random_card_number() -> int:
    """1008 bilan boshlanadigan va jami 16 xonali tasodifiy raqam generatsiya qilish"""
    random_part = "".join([str(random.randint(0, 9)) for _ in range(12)])
    return int("1008" + random_part)

async def create_credit_card(
    db: AsyncSession, 
    user_id: int, 
    initial_balance: Decimal = Decimal("0.00")
) -> CreditCard:
    for _ in range(5):
        card_num = generate_random_card_number()
        new_card = CreditCard(
            user_id=user_id,
            card_number=card_num,
            balance=initial_balance,
            is_frozen=False
        )
        db.add(new_card)
        try:
            await db.commit()
            
            # ✅ User ma'lumotlari bilan birga qayta yuklab olamiz (user_fullname ishlashi uchun)
            stmt = select(CreditCard).options(selectinload(CreditCard.user)).where(CreditCard.id == new_card.id)
            result = await db.execute(stmt)
            return result.scalars().first()
            
        except IntegrityError:
            await db.rollback()
            continue
            
    raise Exception("Karta raqamini generatsiya qilishda xatolik yuz berdi.")


async def get_my_card(db: AsyncSession, user_id: int):
    # ✅ selectinload orqali user ma'lumotlari birga olinadi
    stmt = select(CreditCard).options(selectinload(CreditCard.user)).where(CreditCard.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalars().all()