from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.users import Users
from core.deps import get_current_user
from schemas.device import DeviceTokenCreate, DeviceTokenDelete
from crud.device import save_device_token, delete_device_token

router = APIRouter(prefix="/devices", tags=["Device Tokens"])

@router.post("/register")
async def register_device(
    payload: DeviceTokenCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Foydalanuvchi tizimga kirganda qurilma tokenini saqlash yoki yangilash
    """
    await save_device_token(
        db=db,
        user_id=current_user.id,
        token=payload.token,
        device_type=payload.device_type
    )
    return {
        "message": "Qurilma tokeni muvaffaqiyatli saqlandi",
        "status": status.HTTP_200_OK
    }

@router.delete("/unregister")
async def unregister_device(
    payload: DeviceTokenDelete,
    db: AsyncSession = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """
    Foydalanuvchi akkauntdan chiqqanda (Logout) tokenni o'chirish
    """
    success = await delete_device_token(db=db, token=payload.token, user_id=current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token topilmadi"
        )
        
    return {
        "message": "Qurilma tokeni o'chirildi",
        "status": status.HTTP_200_OK
    }