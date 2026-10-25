from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.users import DeviceToken

async def save_device_token(db: AsyncSession, user_id: int, token: str, device_type: str) -> DeviceToken:
    # Token allaqachon bazada bor-yo'qligini tekshiramiz
    result = await db.execute(select(DeviceToken).where(DeviceToken.token == token))
    device_token = result.scalar_one_or_none()

    if device_token:
        # Agar token boshqa userga tegishli bo'lsa yoki hozirgi userga biriktirilsa
        device_token.user_id = user_id
        device_token.device_type = device_type
        device_token.is_active = True
    else:
        # Yangi token yaratamiz
        device_token = DeviceToken(
            user_id=user_id,
            token=token,
            device_type=device_type,
            is_active=True
        )
        db.add(device_token)

    await db.commit()
    await db.refresh(device_token)
    return device_token

async def delete_device_token(db: AsyncSession, token: str, user_id: int) -> bool:
    result = await db.execute(
        select(DeviceToken).where(DeviceToken.token == token, DeviceToken.user_id == user_id)
    )
    device_token = result.scalar_one_or_none()

    if device_token:
        await db.delete(device_token)
        await db.commit()
        return True
    return False