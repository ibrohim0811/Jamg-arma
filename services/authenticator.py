import os
import httpx
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

AUTHENTICATOR_BASE_URL = "https://api.authenticator.devguard.uz"
AUTHENTICATOR_SERVICE_TOKEN = os.getenv("AUTHENTICATOR_SERVICE_TOKEN")
AUTHENTICATOR_SERVICE_ID = os.getenv("AUTHENTICATOR_SERVICE_ID")

# Yangilangan tokenlarni shu yerda ushlab turamiz
_access_token: str | None = os.getenv("AUTHENTICATOR_ACCESS_TOKEN")
_refresh_token: str | None = os.getenv("AUTHENTICATOR_REFRESH_TOKEN")


async def send_otp_via_service(phone_number: str, otp_code: str):
    global _access_token, _refresh_token

    send_url = f"{AUTHENTICATOR_BASE_URL}/services/messages/send"
    refresh_url = f"{AUTHENTICATOR_BASE_URL}/api/v1/users/refresh"

    payload = {
        "service_id": AUTHENTICATOR_SERVICE_ID,
        "token": AUTHENTICATOR_SERVICE_TOKEN,
        "user_phone": phone_number,
        "message": f"Jamg'arma ilovasiga kirish uchun tasdiqlash kodingiz: {otp_code} Kodni hech kimga bermang !",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            headers = {
                "Authorization": f"Bearer {_access_token}",
                "Content-Type": "application/json",
            }
            response = await client.post(send_url, json=payload, headers=headers)

            # Access token muddati o'tgan bo'lsa — yangilaymiz va so'rovni qayta yuboramiz
            if response.status_code == 401:
                if not _refresh_token:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Authenticator refresh token topilmadi",
                    )

                refresh_res = await client.post(
                    url=refresh_url,
                    json={"refresh_token": _refresh_token},
                )

                if refresh_res.status_code not in (200, 201):
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Tokenni yangilab bo'lmadi: {refresh_res.text}",
                    )

                data = refresh_res.json()
                new_access = data.get("access_token")
                if not new_access:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail="Refresh javobida access_token qaytmadi",
                    )

                # Tokenlarni yangilaymiz
                _access_token = new_access
                if data.get("refresh_token"):
                    _refresh_token = data["refresh_token"]

                # Yangi access_token bilan SMS yuborishni qayta bajaramiz
                headers["Authorization"] = f"Bearer {_access_token}"
                response = await client.post(send_url, json=payload, headers=headers)

            if response.status_code not in (200, 201):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"SMS servisda xatolik: {response.text}",
                )

            return response.json()

        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"SMS servisga ulanib bo'lmadi: {str(e)}",
            )