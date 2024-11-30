from fastapi import APIRouter, Form
from fastapi import FastAPI, HTTPException
import starlette.status as status
from fastapi.responses import RedirectResponse
from schemas import  UserInfoReg, UserInfoAuth
from passlib.context import CryptContext
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.requests import Request
import database1
from database1 import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_email_hash(email: str) -> str:
    return pwd_context.hash(email)
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/registration")
async def registration(email = Form(), username = Form(), password = Form()) -> dict:
    user_dict = {"email":email, "username":username, "password": get_password_hash(password)}
    await create_user(**user_dict)
    return {'message': 'registration succsesful!'}

@router.post("/login")
async def login(email = Form(),password = Form()) -> dict:
    user = await is_email_registered(email=email)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=404, detail="Wrong password")
    return RedirectResponse("/main_page/" + str(user.id),
        status_code=status.HTTP_302_FOUND)