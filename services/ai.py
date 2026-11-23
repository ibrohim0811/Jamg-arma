import json
import os
from typing import Any
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import Users, Transaction
from core.database import get_db
from core.deps import get_current_user


router = APIRouter(prefix="/ai", tags=["AI"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-120b"  # Yoki tezroq: "openai/gpt-oss-20b"


async def ask_groq(messages: list[dict[str, str]], max_tokens: int = 800) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY topilmadi")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(GROQ_URL, headers=headers, json=payload, timeout=25.0)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=f"Groq xatosi: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Tarmoq xatosi: {exc}") from exc


# 1-ENDPOINT: "Tranzaksiyani analiz qilish" tugmasi bosilganda
@router.post("/analyze")
async def analyze_transactions(
    db: AsyncSession = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    # Bazadan user tranzaksiyalarini olamiz (oxirgi 40 tasi)
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(40)
    )
    tx_rows = result.scalars().all()

    if not tx_rows:
        return {"analysis": "Tahlil qilish uchun hali tranzaksiyalar mavjud emas."}

    # ORM obyektlarini oddiy dict ro'yxatiga o'giramiz
    tx_list = [
        {
            "amount": float(tx.amount),
            "type": tx.type,             # masalan: "transfer", "payment", "topup"
            "status": tx.status,
            "date": tx.created_at.strftime("%Y-%m-%d %H:%M"),
        }
        for tx in tx_rows
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "Sen Jamg'arma ilovasining moliyaviy tahlilchisisan. "
                "Berilgan tranzaksiyalar JSON ro'yxatini tahlil qilib, o'zbek tilida qisqa va aniq hisobot ber: "
                "1) Umumiy kirim va chiqim, 2) Asosiy xarajat yo'nalishlari, 3) 2 ta amaliy tavsiya."
            ),
        },
        {
            "role": "user",
            "content": f"Mening tranzaksiyalarim:\n{json.dumps(tx_list, ensure_ascii=False)}",
        },
    ]

    analysis_text = await ask_groq(messages, max_tokens=800)
    return {"analysis": analysis_text}


# 2-ENDPOINT: Oddiy AI chat uchun
class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []  # Oldingi xabarlar: [{"role": "user", "content": "..."}, ...]


@router.post("/chat")
async def ai_chat(
    body: ChatRequest,
    user: Users = Depends(get_current_user),
):
    messages = [
        {
            "role": "system",
            "content": "Sen Jamg'arma fintech ilovasining aqlli yordamchisisisan. O'zbek tilida qisqa va aniq javob ber.",
        },
        *body.history[-10:],  # Oxirgi 10 ta xabarni kontekst sifatida qo'shamiz
        {"role": "user", "content": body.message},
    ]

    reply = await ask_groq(messages, max_tokens=600)
    return {"reply": reply}