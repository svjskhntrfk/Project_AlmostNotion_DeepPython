import starlette.status as status
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext


from database1 import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates = Jinja2Templates(directory="templates")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
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
    password2: str = Form(...)
):
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
        existing_user = await is_email_registered(email)
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

        await create_user(**user_dict)
        user = await is_email_registered(email=email)
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
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        # Проверяем существование пользователя
        user = await is_email_registered(email=email)
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
async def check_email(email: str):
    user = await is_email_registered(email)
    return {"exists": user is not None}