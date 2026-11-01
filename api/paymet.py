from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from core.database import get_db 
from models.users import Users  
from schemas.card import CardResponse, GetCardNumberSchema
from crud.card import create_credit_card, freeze_my_card, get_my_card, unfreeze_my_card
from core.deps import get_current_user


