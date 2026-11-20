import os
from typing import Any
import httpx
from fastapi import APIRouter, HTTPException, Query

app = APIRouter(prefix="/info")

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
POPULAR_STOCKS = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA"]


async def fetch_json(client: httpx.AsyncClient, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = await client.get(url, params=params, timeout=10.0)
    resp.raise_for_status()
    return resp.json()


@app.get("/currencies")
async def get_currencies(base: str = Query(default="USD", min_length=3, max_length=3)):
    """USD, EUR, RUB kurslarini qaytaradi (masalan: base=USD yoki base=UZS)."""
    base = base.upper()
    targets = ["USD", "EUR", "RUB"]
    async with httpx.AsyncClient() as client:
        try:
            data = await fetch_json(client, f"https://open.er-api.com/v6/latest/{base}")
            rates = data.get("rates", {})
            selected = {cur: rates.get(cur) for cur in targets if cur in rates}
            return {
                "base": base,
                "provider": "open.er-api.com",
                "rates": selected,
            }
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Valyuta API xatosi: {exc}") from exc


@app.get("/crypto")
async def get_crypto():
    """BTC va USDT bozor ma'lumotlarini (narx, 24h o'zgarish, volume) qaytaradi."""
    async with httpx.AsyncClient() as client:
        try:
            btc_ticker = await fetch_json(
                client,
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": "BTCUSDT"},
            )
            usdt_data = await fetch_json(
                client,
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "tether",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                },
            )
            tether = usdt_data.get("tether", {})
            return {
                "BTC": {
                    "pair": "BTC/USDT",
                    "price_usdt": float(btc_ticker["lastPrice"]),
                    "price_change_pct_24h": float(btc_ticker["priceChangePercent"]),
                    "high_24h": float(btc_ticker["highPrice"]),
                    "low_24h": float(btc_ticker["lowPrice"]),
                    "volume_24h_btc": float(btc_ticker["volume"]),
                },
                "USDT": {
                    "price_usd": tether.get("usd"),
                    "price_change_pct_24h": tether.get("usd_24h_change"),
                    "volume_24h_usd": tether.get("usd_24h_vol"),
                },
            }
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Kripto API xatosi: {exc}") from exc


@app.get("/stocks")
async def get_stocks(symbols: str = Query(default="AAPL,MSFT,NVDA,GOOGL,TSLA")):
    """Apple (AAPL) va boshqa mashhur aksiyalar bo'yicha ma'lumot qaytaradi."""
    ticker_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] or POPULAR_STOCKS

    if not FINNHUB_API_KEY:
        return {
            "note": "Real vaqt aksiyalar narxi uchun FINNHUB_API_KEY muhit o'zgaruvchisini o'rnating (bepul kalit finnhub.io dan olinadi).",
            "requested_symbols": ticker_list,
            "stocks": {},
        }

    results: dict[str, Any] = {}
    async with httpx.AsyncClient() as client:
        for sym in ticker_list:
            try:
                quote = await fetch_json(
                    client,
                    "https://finnhub.io/api/v1/quote",
                    params={"symbol": sym, "token": FINNHUB_API_KEY},
                )
                results[sym] = {
                    "current_price": quote.get("c"),
                    "change": quote.get("d"),
                    "change_pct": quote.get("dp"),
                    "high_of_day": quote.get("h"),
                    "low_of_day": quote.get("l"),
                    "prev_close": quote.get("pc"),
                }
            except httpx.HTTPError as exc:
                results[sym] = {"error": str(exc)}

    return {"provider": "finnhub.io", "stocks": results}


@app.get("/market")
async def get_all_market(base: str = Query(default="USD", min_length=3, max_length=3)):
    """Barcha ma'lumotlarni (valyuta, BTC/USDT, aksiyalar) bitta javobda qaytaradi."""
    currencies = await get_currencies(base=base)
    crypto = await get_crypto()
    stocks = await get_stocks()
    return {
        "currencies": currencies,
        "crypto": crypto,
        "stocks": stocks,
    }