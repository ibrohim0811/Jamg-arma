from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def welcome():
    return {"message":"Welcome to Jamgarma", "requirements":"You should installed Autheticator app for register to this app!", "source":"You will install authenticator from https://devguard.uz  Good Luck!"}