import starlette.status as status
from fastapi import APIRouter, Form, Depends, Request
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from database import create_board, get_board_by_user_id_and_board_id, create_text, get_session
from fastapi import APIRouter, Depends, Request, Security
from fastapi.responses import JSONResponse

from auth.middlewares.jwt.service import check_access_token
from auth.service import AuthService
from auth.middlewares.jwt.base.auth import JWTAuth
from auth.transport.responses import TokensOut
from auth.errors import AuthErrorTypes
from auth.jwt_settings import jwt_config

from pydantic import BaseModel


class SuccessOut(BaseModel):
    success: bool = True


class ErrorOut(BaseModel):
    type: str
    message: str

from database import *
from auth.dto import UserCredentialsDTO

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

def get_auth_service() -> AuthService:
    return AuthService(jwt_auth=JWTAuth(config=jwt_config))

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

@router.post(
    path='/registration',
    responses={
        200: {'model': TokensOut},
        400: {'model': ErrorOut},
    },
)
async def registration(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    password2: str = Form(...), 
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service)):
    """
    Post-запрос, забираем данные пользователя с регистрации.
    """
    try:
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

        user_credentials = UserCredentialsDTO(
            email=email,
            password=password
        )

        # Use AuthService to register the user
        print(user_credentials)
        tokens, error = await auth_service.register(user_credentials, username, session)
        print(tokens)
        print(error)
        if error:
            if error.type == AuthErrorTypes.EMAIL_OCCUPIED:
                return templates.TemplateResponse(
                    "reg.html",
                    {
                        "request": request,
                        "email_error": "Этот email уже зарегистрирован",
                        "username": username
                    }
                )
            return templates.TemplateResponse(
                "reg.html",
                {
                    "request": request,
                    "error": error.message,
                    "email": email,
                    "username": username
                }
            )

        # Получаем созданного пользователя
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
async def login(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...), 
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service)):
    """
    Авторизация пользователя
    """
    try:
        # Создаем DTO для входа
        user_credentials = UserCredentialsDTO(
            email=email,
            password=password
        )

        # Пытаемся войти через AuthService
        tokens, error = await auth_service.login(user_credentials)
        
        if error:
            # Если неверные учетные данные
            if error.type == AuthErrorTypes.INVALID_CREDENTIALS:
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "password_error": "Неверный email или пароль",
                        "email": email
                    }
                )
            # Если другая ошибка
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": error.message,
                    "email": email
                }
            )

        # Получаем пользователя для редиректа
        user = await is_email_registered(email=email, session=session)
        
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