import re
from pydantic import BaseModel, Field, field_validator

class UserCreate(BaseModel):
    first_name: str = Field(..., max_length=350)
    last_name: str = Field(..., max_length=350)
    phone_number: str = Field(..., description="O'zbekiston telefon raqami, masalan: +998901234567")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # O'zbekiston telefon raqamlari uchun regex pattern (+998 bilan boshlanib, jami 13 ta belgi bo'lishi)
        pattern = r"^\+998\d{9}$"
        
        if not re.match(pattern, v):
            raise ValueError("Telefon raqam noto'g'ri formatda. Namuna: +998901234567")
        
        return v

class UserRead(BaseModel):
    id: int
    first_name: str
    last_name: str
    phone_number: str
    is_active: bool

    class Config:
        from_attributes = True



class LoginSchema(BaseModel):
    phone_number: str
    password: str