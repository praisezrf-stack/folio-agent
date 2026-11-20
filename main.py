from fastapi import FastAPI, UploadFile, File
from folioAgent.api.auth import login, register
from pydantic import BaseModel

app = FastAPI()

class LoginRequest(BaseModel):
    name:str
    password:str

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def user_login(data:LoginRequest):
    return login(data.name, data.password)


@app.post("/register")
def user_register(data:LoginRequest):
    return register(data.name, data.password)


