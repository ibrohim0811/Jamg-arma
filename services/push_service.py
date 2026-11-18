import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import DeviceToken  # O'zingning model importing

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

async def send_expo_push(
    db: AsyncSession,
    user_id: int,
    title: str,
    body: str,
    data: dict | None = None
):
    # 1. Userning faol tokenlarini bazadan olamiz
    result = await db.execute(
        select(DeviceToken).where(
            DeviceToken.user_id == user_id,
            DeviceToken.is_active == True
        )
    )
    devices = result.scalars().all()
    if not devices:
        return

    # 2. Expo formatidagi xabarlar ro'yxatini tuzamiz
    messages = []
    valid_devices = []
    for device in devices:
        if device.token.startswith("ExponentPushToken[") or device.token.startswith("ExpoPushToken["):
            messages.append({
                "to": device.token,
                "sound": "default",
                "title": title,
                "body": body,
                "data": data or {},
                "priority": "high"
            })
            valid_devices.append(device)

    if not messages:
        return

    # 3. Expo serveriga asinxron so'rov yuboramiz
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(EXPO_PUSH_URL, json=messages, headers=headers)
            res_data = response.json()

        # 4. Eskirgan yoki o'chirilgan qurilmalarni tekshirib, o'chirib qo'yamiz
        tickets = res_data.get("data", [])
        for idx, ticket in enumerate(tickets):
            if ticket.get("status") == "error":
                error_type = ticket.get("details", {}).get("error")
                if error_type == "DeviceNotRegistered":
                    valid_devices[idx].is_active = False
                    db.add(valid_devices[idx])

        await db.commit()
    except Exception as e:
        print(f"Expo Push xatoligi: {e}")