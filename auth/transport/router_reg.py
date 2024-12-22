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

from fastapi.responses import HTMLResponse

from email_validator import validate_email, EmailNotValidError
import dns.resolver
import asyncio
import logging

logger = logging.getLogger(__name__)

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

async def is_valid_email_domain(email: str) -> bool:
    """Check if email domain exists and can accept emails."""
    try:
        # Get domain from email
        domain = email.split('@')[1]
        
        # Try to get MX records for the domain
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return False
            
    except Exception as e:
        logger.error(f"Error checking email domain: {str(e)}")
        return False

async def validate_email_address(email: str) -> tuple[bool, str]:
    """
    Validate email address format and domain.
    Returns (is_valid, error_message)
    """
    try:
        # Check email format
        validation = validate_email(email, check_deliverability=False)
        email = validation.normalized
        
        # Check if domain can accept emails
        if not await is_valid_email_domain(email):
            return False, "Email domain cannot receive emails"
            
        return True, ""
        
    except EmailNotValidError as e:
        return False, str(e)
    except Exception as e:
        logger.error(f"Error validating email: {str(e)}")
        return False, "Invalid email address"

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
        logger.info(f"Starting registration for email: {email}")
        
        # Validate passwords match
        if password != password2:
            logger.warning("Password mismatch during registration")
            return templates.TemplateResponse(
                "reg.html",
                {
                    "request": request,
                    "password2_error": "Пароли не совпадают",
                    "email": email,
                    "username": username
                }
            )

        # Validate email
        is_valid, error_message = await validate_email_address(email)
        if not is_valid:
            logger.warning(f"Invalid email during registration: {error_message}")
            return templates.TemplateResponse(
                "reg.html",
                {
                    "request": request,
                    "email_error": f"Неверный email: {error_message}",
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
                logger.warning(f"Email already registered: {email}")
                return templates.TemplateResponse(
                    "reg.html",
                    {
                        "request": request,
                        "email_error": "Этот email уже зарегистрирован",
                        "username": username
                    }
                )
            logger.error(f"Registration error: {error.message}")
            return templates.TemplateResponse(
                "reg.html",
                {
                    "request": request,
                    "error": error.message,
                    "email": email,
                    "username": username
                }
            )

        logger.info(f"Successfully registered user with email: {email}")
        return RedirectResponse(
            url=f"/login",
            status_code=status.HTTP_302_FOUND
        )

    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
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

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Отображает страницу входа

    Параметры:
        request (Request): Объект HTTP-запроса.
    """
    return templates.TemplateResponse("entry.html", {"request": request})

@router.get("/registration", response_class=HTMLResponse)
async def registration_page(request: Request):
    """
    Get-запрос, отображает страницу регистрации

    Параметры:
        request (Request): Объект HTTP-запроса
    """
    return templates.TemplateResponse("reg.html", {"request": request})