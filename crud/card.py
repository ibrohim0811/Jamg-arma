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


async def find_card_by_number(db: AsyncSession, card_number_str: str) -> CreditCard | None:
    """
    Karta raqami bo'yicha qidirish va uning egasining ma'lumotlarini birga olish (eager loading)
    """
    try:
        # Kiritilgan matnni BigInteger ga moslab int ga o'tkazamiz
        card_number_int = int(card_number_str.strip())
    except ValueError:
        return None  # Agar karta raqami harflardan iborat bo'lib qolsa

    # So'rovni tuzamiz (User ma'lumotlari birga kelishi uchun selectinload ishlatamiz)
    stmt = (
        select(CreditCard)
        .options(selectinload(CreditCard.user))
        .where(CreditCard.card_number == card_number_int)
    )
    
    result = await db.execute(stmt)
    card = result.scalar_one_or_none()
    
    return card


import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.users import CreditCard, Transaction, TransactionType, Users  # o'z import yo'lingga mosla


async def get_user_card_by_identifier(
    db: AsyncSession,
    user_id: int,
    card_identifier: str,
    for_update: bool = False,
) -> CreditCard | None:
    """Foydalanuvchi kartasini UUID (id) yoki 16 xonali karta raqami (card_number) orqali topish."""
    cleaned = str(card_identifier).strip()
    if not cleaned:
        return None

    condition = None
    try:
        card_uuid = uuid.UUID(cleaned)
        condition = CreditCard.id == card_uuid
    except ValueError:
        if cleaned.isdigit():
            condition = CreditCard.card_number == int(cleaned)

    if condition is None:
        return None

    stmt = select(CreditCard).where(condition, CreditCard.user_id == user_id)
    if for_update:
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def top_up_card(
    db: AsyncSession,
    current_user: Users,
    card_id: str,
    amount: Decimal,
    description: str | None = "Kartani to'ldirish",
) -> dict:
    if amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summa 0 dan katta bo'lishi kerak",
        )

    # Kartani lock bilan olish (parallel so'rovlarda balans buzilmasligi uchun)
    card = await get_user_card_by_identifier(
        db=db,
        user_id=current_user.id,
        card_identifier=card_id,
        for_update=True,
    )

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Karta topilmadi yoki sizga tegishli emas",
        )

    if card.is_frozen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Karta muzlatilgan, to'ldirib bo'lmaydi",
        )

    # Balansni yangilash
    card.balance = (Decimal(str(card.balance)) + amount).quantize(Decimal("0.01"))

    # Tranzaksiya yaratish
    transaction = Transaction(
        sender_card_id=None,
        receiver_card_id=card.id,
        amount=amount.quantize(Decimal("0.01")),
        currency="UZS",
        status="success",
        transaction_type=TransactionType.REPLENISHMENT.value,
        description=description or "Kartani to'ldirish",
    )
    db.add(transaction)

    await db.commit()
    await db.refresh(card)
    await db.refresh(transaction)

    return {
        "transaction_id": str(transaction.id),
        "card_id": str(card.id),
        "amount": transaction.amount,
        "new_balance": card.balance,
        "status": transaction.status,
        "transaction_type": transaction.transaction_type,
        "created_at": transaction.created_at,
    }