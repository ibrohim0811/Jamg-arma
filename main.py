from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth
from api.device import router as device
from api.card import router as card
from api.communal import router as payment
from api.telecom import router as telecom
from api.p2p import router as p2p
from api.transaction import router as transaction
from api.currency import app as currency

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth)
app.include_router(device)
app.include_router(card)
app.include_router(payment)
app.include_router(p2p)
app.include_router(telecom)
app.include_router(transaction)
app.include_router(currency)


@app.get("/")
async def welcome():
    return {"message":"Welcome to Jamgarma", "requirements":"You should installed Autheticator app for register to this app!", "source":"You will install authenticator from https://devguard.uz  Good Luck!"}