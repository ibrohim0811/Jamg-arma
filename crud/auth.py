from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.users import Users  # O'zingizning modellaringiz joylashgan fayldan import qiling
from schemas.auth import UserCreate

async def get_user_by_id(db: AsyncSession, user_id: int) -> Users | None:
    """ID bo'yicha foydalanuvchini topish"""
    result = await db.execute(select(Users).where(Users.id == user_id))
    return result.scalars().first()

async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Users | None:
    """Telefon raqam bo'yicha foydalanuvchini topish"""
    result = await db.execute(select(Users).where(Users.phone_number == phone_number))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate, hashed_password: str) -> Users:
    """Yangi foydalanuvchi yaratish"""
    db_user = Users(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        phone_number=user_in.phone_number,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Users]:
    """Barcha foydalanuvchilarni ro'yxat olish"""
    result = await db.execute(select(Users).offset(skip).limit(limit))
    return result.scalars().all()