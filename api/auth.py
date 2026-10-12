from fastapi import APIRouter

from core.database import get_db
from schemas.auth import UserCreate, UserRead
from crud.auth import create_user, get_all_users, get_user_by_id, get_user_by_phone

