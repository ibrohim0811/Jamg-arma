from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db 
from models.users import Users  # Users modelini to'g'ri import qilamiz
from schemas.card import CardResponse, GetCardNumberSchema
from crud.card import create_credit_card, freeze_my_card, get_my_card, unfreeze_my_card
from core.deps import get_current_user

router = APIRouter(prefix="/cards", tags=["Credit Cards"])

# 1. Karta ochish (Create Card)
@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card_endpoint(
    user: Users = Depends(get_current_user),  
    db: AsyncSession = Depends(get_db)
):
    try:
        new_card = await create_credit_card(db=db, user_id=user.id)
        return new_card
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Servis vaqtinchalik ishlamayabdi! Xato: {str(e)}"
        )

# 2. Kartani muzlatish (Freeze Card)
@router.patch("/freeze", response_model=CardResponse)
async def freeze_card_endpoint(
    payload: GetCardNumberSchema,
    user: Users = Depends(get_current_user),  # ✅ Depends() qo'shildi
    db: AsyncSession = Depends(get_db)
):
    try:
        updated_card = await freeze_my_card(db=db, user_id=user.id, card_number=payload.card_number)
        return updated_card
    except HTTPException as he:
        raise he  # Agar CRUD ichidan aniq 404 yoki 400 chiqqan bo'lsa, o'zini qaytaramiz
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servis vaqtincha ishlamayabdi!"
        )


@router.patch("/unfreeze", response_model=CardResponse)
async def freeze_card_endpoint(
    payload: GetCardNumberSchema,
    user: Users = Depends(get_current_user),  # ✅ Depends() qo'shildi
    db: AsyncSession = Depends(get_db)
):
    try:
        updated_card = await unfreeze_my_card(db=db, user_id=user.id, card_number=payload.card_number)
        return updated_card
    except HTTPException as he:
        raise he  # Agar CRUD ichidan aniq 404 yoki 400 chiqqan bo'lsa, o'zini qaytaramiz
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servis vaqtincha ishlamayabdi!"
        )

# 3. Userning barcha kartalarini olish (Get My Cards)
@router.get("/", response_model=List[CardResponse])
async def get_user_cards(
    user: Users = Depends(get_current_user),  # ✅ Depends() qo'shildi
    db: AsyncSession = Depends(get_db)
):
    try:
        cards = await get_my_card(db=db, user_id=user.id)
        return cards
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Servis vaqtincha ishlamayabdi"
        )