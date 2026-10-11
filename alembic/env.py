import os
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from dotenv import load_dotenv

load_dotenv()

# 1. Loyihangizdagi sozlamalar va Base modelini import qiling
from core.database import Base  # Barcha modellaringiz Base ga bog'langan bo'lishi kerak


# Alembic Config obyekti (alembic.ini faylidagi qiymatlar)
config = context.config
DATABASE_URL = os.getenv("DATABASE_URL")

# Logging sozlamalari
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Modellaringiz metadata'sini ko'rsating (autogenerate to'g'ri ishlashi uchun)
target_metadata = Base.metadata

# 3. DATABASE_URL ni dinamik ravishda o'rnatamiz
config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Offline rejimda migratsiya yurgizish (DB bilan to'g'ridan-to'g'ri ulanmasdan SQL yaratish)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Migratsiyalarni bajaruvchi asosiy funksiya."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # async_engine_from_config o'rniga create_async_engine ishlatamiz
    connectable = create_async_engine(
        DATABASE_URL,
        poolclass=pool.NullPool,
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        },
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online rejimda migratsiyalarni yurgizish."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()