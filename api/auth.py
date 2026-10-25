import os
import json
import jwt
from random import randint
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from upstash_redis import Redis
from models.users import Users
from schemas.auth import UserCreate, LoginSchema, ConfirmOTPSchema, UserSaveSchema, UserRead, RefreshTokenSchema
from crud.auth import create_user, get_user_by_phone
from core.deps import get_current_user, decode_token
from sqlalchemy.future import select
from core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from dotenv import load_dotenv
from services.authenticator import send_otp_via_service

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth Services"])

redis = Redis(url=os.getenv("UPSTASH_URL"), token=os.getenv("UPSTASH_TOKEN"))


@router.post("/login")
async def login(schema: LoginSchema, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_phone(db, phone_number=schema.phone_number)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telefon raqam yoki parol noto'g'ri"
        )
    
    if not verify_password(schema.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Telefon raqam yoki parol noto'g'ri"
        )

    # Token ichiga foydalanuvchining UUID ID sini string ko'rinishida yozamiz
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "message": "Muvaffaqiyatli kirildi",
        "user_id": user.id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.post("/register")
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Foydalanuvchi bazada bor-yo'qligini tekshirish
    existing_user = await get_user_by_phone(phone_number=payload.phone_number, db=db)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Bu telefon raqam avval ro'yxatdan o'tgan"
        )

    # 2. Parolni xeshlab, ma'lumotlarni tayyorlaymiz
    hashed_password = get_password_hash(payload.password)
    
    user_data = {
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "phone_number": payload.phone_number,
        "hashed_password": hashed_password
    }

    # 3. Redis'ga vaqtinchalik saqlaymiz (3 minut - 180 sekund)
    redis.set(
        key=payload.phone_number, 
        value=json.dumps(user_data), 
        ex=180
    )

    # 4. OTP generatsiya qilish va jo'natish
    otp_code = randint(100000, 999999)
    await send_otp_via_service(phone_number=payload.phone_number, otp_code=str(otp_code))

    # 5. OTP'ni Redis'ga yozish
    redis.set(key=f"otp:{payload.phone_number}", value=otp_code, ex=180)

    return {
        "message": f"Tasdiqlash kodi Authenticator ilovasiga {payload.phone_number} ga yuborildi!",
        "status": status.HTTP_200_OK
    }


@router.post("/confirm-otp")
async def confirm_otp(payload: ConfirmOTPSchema, db: AsyncSession = Depends(get_db)):
    # 1. Redis'dan OTP ni tekshirish
    generated_otp = redis.get(f"otp:{payload.phone_number}")

    if not generated_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kod muddati o'tgan yoki topilmadi")

    if int(payload.otp_code) != int(generated_otp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kod yaroqsiz yoki noto'g'ri")

    # 2. Redis'dan user ma'lumotlarini olish
    user_json = redis.get(payload.phone_number)
    if not user_json:
        raise HTTPException(status_code=400, detail="Ro'yxatdan o'tish muddati tugagan, qaytadan ro'yxatdan o'ting")
    
    user_json_str = user_json.decode("utf-8") if isinstance(user_json, bytes) else user_json
    user_data = json.loads(user_json_str)
    
    hashed_password = user_data["hashed_password"]
    
    # 3. Pydantic modelga o'tkazib bazaga saqlash
    user_schema = UserSaveSchema(
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        phone_number=user_data["phone_number"]
    )
    
    user = await create_user(db=db, user_in=user_schema, hashed_password=hashed_password)
    
    # 4. Token yaratish
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # 5. Redis'ni tozalash
    redis.delete(payload.phone_number)
    redis.delete(f"otp:{payload.phone_number}")

    return {
        "message": "Muvaffaqiyatli ro'yxatdan o'tdingiz",
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/me", response_model=UserRead)
async def getme(user: Users = Depends(get_current_user)):
    return user


@router.post("/refresh")
async def refresh_access_token(payload: RefreshTokenSchema, db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token yaroqsiz yoki muddati o'tgan!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Tokenni dekod qilamiz
        token_payload = decode_token(payload.refresh_token)
        
        # Token turi "refresh" ekanligini tekshiramiz
        if token_payload.get("type") != "refresh":
            raise credentials_exception
            
        user_id = token_payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except jwt.PyJWTError:
        raise credentials_exception

    # Foydalanuvchi bazada hali ham mavjudligini tekshiramiz
    try:
        result = await db.execute(select(Users).where(Users.id == int(user_id)))
    except ValueError:
        result = await db.execute(select(Users).where(Users.phone_number == user_id))
        
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    # Yangi Access Token yaratamiz (Refresh tokenning o'zi o'zgarmasdan qoladi yoki yangisini ham berishingiz mumkin)
    new_access_token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }