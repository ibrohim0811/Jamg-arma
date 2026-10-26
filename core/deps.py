import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from crud.auth import check_admin
from models.users import Users
from core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token yaroqsiz yoki muddati o'tgan!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    # ID raqam (Integer) ekanligini hisobga olib int ga o'giramiz
    try:
        result = await db.execute(select(Users).where(Users.id == int(user_id)))
    except ValueError:
        # Agar sub raqam bo'lmasa (masalan, eski token uchun telefon raqam bo'lsa)
        result = await db.execute(select(Users).where(Users.phone_number == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_admin(
    current_user: Users = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Users:
    
    # O'zingiz yozgan check_admin funksiyasini chaqiramiz
    is_admin = await check_admin(db, current_user.id)
    
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu amalni bajarish uchun sizda admin huquqi yo'q."
        )
        
    return current_user