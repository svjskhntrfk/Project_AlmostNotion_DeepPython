from fastapi import APIRouter
from fastapi import FastAPI, HTTPException
from schemas import  UserInfoReg, UserInfoAuth
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.requests import Request
import database1
from database1 import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/registration")
async def registration(user_data: UserInfoReg) -> dict:
    user_dict = user_data.dict()
    user_dict['password'] = get_password_hash(user_data.password)
    await create_user(**user_dict)
    return {'message': 'Вы успешно зарегистрированы!'}

@router.post("/login")
async def login(user_data: UserInfoAuth) -> dict:
    user = await is_email_registered(email=user_data.email)
    if not user:
        # TODO FOR MARIA if user not in the table
        raise HTTPException(status_code=404, detail="Email not found")
    if not verify_password(user_data.password, user.password):
        # TODO FOR MARIA if passwords dont match
        raise HTTPException(status_code=404, detail="Email not found")
    return {'message': 'Вы успешно зашли в аккаунт!'}