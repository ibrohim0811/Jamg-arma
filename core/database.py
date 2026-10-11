import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") 

# Asinxron engine yaratamiz
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        # Transaction Pooler (PgBouncer) bilan ishlash uchun statement keshlashni o'chiramiz:
        "prepared_statement_cache_size": 0,
    }
)

# Async Session yaratish uchun fabrikasi
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# FastAPI endpoint'larida session olish uchun Dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

class Base(DeclarativeBase):
    pass