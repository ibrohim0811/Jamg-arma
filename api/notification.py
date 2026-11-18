from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from models.users import DeviceToken, Users
from core.deps import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])

class TokenRegisterSchema(BaseModel):
    token: str = Field(..., max_length=500)
    device_type: str = Field(..., max_length=20)  # 'android' yoki 'ios'

@router.post("/register-token", status_code=status.HTTP_200_OK)
async def register_token(
    payload: TokenRegisterSchema,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    result = await db.execute(
        select(DeviceToken).where(DeviceToken.token == payload.token)
    )
    existing_token = result.scalar_one_or_none()

    if existing_token:
        existing_token.user_id = current_user.id
        existing_token.device_type = payload.device_type
        existing_token.is_active = True
    else:
        new_token = DeviceToken(
            user_id=current_user.id,
            token=payload.token,
            device_type=payload.device_type,
            is_active=True
        )
        db.add(new_token)

    await db.commit()
    return {"status": "ok", "message": "Token saqlandi"}


@router.delete("/remove-token", status_code=status.HTTP_200_OK)
async def remove_token(
    token: str,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    result = await db.execute(
        select(DeviceToken).where(
            DeviceToken.token == token,
            DeviceToken.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()

    if device:
        device.is_active = False
        await db.commit()

    return {"status": "ok", "message": "Token o'chirildi"}