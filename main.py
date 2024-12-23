from contextlib import asynccontextmanager
from fastapi import Depends
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from starlette.requests import Request
from starlette.responses import HTMLResponse

from src.db import *
from src.backend.auth.transport.router_reg import router as reg_router
from src.backend.router.router_boards import router as board_router
from src.backend.router.router_profile import router as profile_router
from src.backend.router.router_image import  router as image_router
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Хэшируем пароль с использованием bcrypt.

    Параметры:
        password (str): Пароль, который нужно хэшировать.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля его хэшированному значению

    Параметры:
        plain_password (str): Исходный пароль.
        hashed_password (str): Хэшированное значение пароля
    """
    return pwd_context.verify(plain_password, hashed_password)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер, который управляет жизненным циклом приложения
    """
    await create_tables(engine)
    print("База готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)
app.include_router(reg_router)
app.include_router(board_router)
app.include_router(profile_router)
app.include_router(image_router)

app.mount("/static", StaticFiles(directory="src/front/static"), name="static")

templates = Jinja2Templates(directory="src/front/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Get-запрос, отображает главную страницу

    Параметры:
        request (Request): Объект HTTP-запроса
    """
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/registration", response_class=HTMLResponse)
async def registration_page(request: Request):
    """
    Get-запрос, отображает страницу регистрации

    Параметры:
        request (Request): Объект HTTP-запроса
    """
    return templates.TemplateResponse("reg.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Отображает страницу входа

    Параметры:
        request (Request): Объект HTTP-запроса.
    """
    return templates.TemplateResponse("entry.html", {"request": request})


