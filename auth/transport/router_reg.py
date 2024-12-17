import starlette.status as status
from fastapi import APIRouter, Form, Depends, Request
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
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

templates = Jinja2Templates(directory="templates")

def get_auth_service() -> AuthService:
    return AuthService(jwt_auth=JWTAuth(config=jwt_config))


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
    Post-запрос, забиваем данные пользователя с регистрации.
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
        tokens, error = await auth_service.register(user_credentials, username, session)
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
        
        return RedirectResponse(
            url=f"/login",
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
        user_credentials = UserCredentialsDTO(
            email=email,
            password=password
        )

        tokens, error = await auth_service.login(user_credentials, session=session)
        
        if error:
            if error.type == AuthErrorTypes.INVALID_CREDENTIALS:
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "password_error": "Неверный email или пароль",
                        "email": email
                    }
                )
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": error.message,
                    "email": email
                }
            )
        
        response = RedirectResponse(
            f"/profile/main_page",
            status_code=status.HTTP_302_FOUND
        )
        
        response.set_cookie(
            key="Authorization",
            value=f"Bearer {tokens.access_token}",
            httponly=True
        )
        
        return response

    except Exception as e:
        return {
                "request": request,
                "user":request.state.user,
                "error": e
            }


@router.get("/check_email/{email}")
async def check_email(email: str, session: AsyncSession = Depends(get_session)):
    user = await is_email_registered(email, session)
    return {"exists": user is not None}
