import os
import httpx
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

AUTHENTICATOR_SERVICE_TOKEN=os.getenv("AUTHENTICATOR_SERVICE_TOKEN")
AUTHENTICATOR_ACCESS_TOKEN=os.getenv("AUTHENTICATOR_ACCESS_TOKEN")
AUTHENTICATOR_SERVICE_ID=os.getenv("AUTHENTICATOR_SERVICE_ID")


async def send_otp_via_service(phone_number: str, otp_code: str):
    url = "https://api.authenticator.devguard.uz/services/messages/send"
    
    # Servis talab qilayotgan aniq payload strukturasi
    payload = {
        "service_id": AUTHENTICATOR_SERVICE_ID,  # O'zingizning haqiqiy service_id ingizni yozasiz
        "token": AUTHENTICATOR_SERVICE_TOKEN,                        # O'zingizning service tokeningiz
        "user_phone": phone_number,
        "message": f"Jamg'arma ilovasiga kirish uchun tasdiqlash kodingiz: {otp_code} Kodni hech kimga bermang !"
    }
    
    headers = {
        "Authorization": f"Bearer {AUTHENTICATOR_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=10.0)
            
            # Agar javob muvaffaqiyatli bo'lmasa
            if response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"SMS servisda xatolik: {response.text}"
                )
                
            return response.json()
            
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"SMS servisga ulanib bo'lmadi: {str(e)}"
            )