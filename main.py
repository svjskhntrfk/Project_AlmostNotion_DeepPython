from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from database_1 import create_table, add_user, is_email_registered
from router import router as users_router
from schemas import  UserInfoReg, UserInfoAuth

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
from starlette.requests import Request
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    print("База готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)
app.include_router(users_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})
@app.post("/registration")
async def registration(user_data: UserInfoReg) -> dict:
    user_dict = user_data.dict()
    user_dict['password'] = get_password_hash(user_data.password)
    await add_user(**user_dict[:-2])
    return {'message': 'Вы успешно зарегистрированы!'}
@app.post("/login", response_class=HTMLResponse)
async def login(user_data: UserInfoAuth) -> dict:
    user = await is_email_registered(email=user_data.email)
    if not user:
        # TODO FOR MARIA if user not in the table
        raise HTTPException(status_code=404, detail="Email not found")
        #return {'message': 'Пользователь с таким email не найден.'}
    if not verify_password(user_data.password, user.password):
        # TODO FOR MARIA if passwords dont match
        raise HTTPException(status_code=404, detail="Email not found")
        # return {'message': 'Неверный пароль.'}
    return {'message': 'Вы успешно зашли в аккаунт!'}

