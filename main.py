from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth
from api.device import router as device
from api.card import router as card
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


@app.get("/")
async def welcome():
    return {"message":"Welcome to Jamgarma", "requirements":"You should installed Autheticator app for register to this app!", "source":"You will install authenticator from https://devguard.uz  Good Luck!"}