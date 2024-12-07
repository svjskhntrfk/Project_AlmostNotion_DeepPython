import starlette.status as status
from fastapi import APIRouter, Form, Depends, Request
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from database import create_board, get_board_by_user_id_and_board_id, create_text, get_session

from database import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

def get_password_hash(password: str) -> str:
    """
    Хэшируем пароль пользователя

    Параметры:
        password (str): Пароль, который надо хэшировать
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяем пароль при входе в аккаунт с помощью хэшей

    Параметры:
        plain_password (str): Пароль, который надо проверить на совпадение
        hashed_password (str): Хэшированный пароль
    """
    return pwd_context.verify(plain_password, hashed_password)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/registration")
async def registration(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...), 
    session: AsyncSession = Depends(get_session)):
    """
        Post-запрос, забираем данные пользователя с регистрации. Проверяем, что пользователь не был зарегистрирован ранее и совпадение повторного пароля с изначальным

        Параметры:
            email (Form): Почта пользователя
            username (Form): Имя пользователя
            password (Form): Пароль
            password2 (Form): Подтверждение пароля
            session (AsyncSession): Сессия в базе данных
    """
    try:
        # Проверяем, что пароли совпадают
        if password != password2:
            return templates.TemplateResponse(
                "reg.html",
                {
                    "request": request,
                    "password2_error": "Пароли не совпадают",
                    "email": email,
                    "username": username
                }
            )

        # Проверяем, что email не занят
        existing_user = await is_email_registered(email, session)
        if existing_user:
            return templates.TemplateResponse(
                "reg.html",
                {
                    "request": request,
                    "email_error": "Этот email уже зарегистрирован",
                    "username": username
                }
            )

        # Создаем пользователя
        user_dict = {
            "email": email,
            "username": username,
            "password": get_password_hash(password)
        }

        await create_user(**user_dict, session=session)
        user = await is_email_registered(email=email, session=session)
        return RedirectResponse(
            f"/main_page/{user.id}",
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        return templates.TemplateResponse(
            "reg.html",
            {
                "request": request,
                "error": "Произошла ошибка при регистрации",
                "email": email,
                "username": username
            }
        )

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_session)):
    """
    Авторизация пользователя

    Параметры:
        email (Form): Почта пользователя
        password (Form): Пароль пользователя
        session (AsyncSession): Сессия в базе данных
    """
    try:
        # Проверяем существование пользователя
        user = await is_email_registered(email=email, session=session)
        if not user:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "email_error": "Пользователь с таким email не найден"
                }
            )

        # Проверяем правильность пароля
        if not verify_password(password, user.password):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "password_error": "Неверный пароль",
                    "email": email  # Сохраняем введенный email
                }
            )

        return RedirectResponse(
            f"/main_page/{user.id}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Произошла ошибка при входе в систему"
            }
        )

@router.get("/check_email/{email}")
async def check_email(email: str, session: AsyncSession = Depends(get_session)):
    user = await is_email_registered(email, session)
    return {"exists": user is not None}