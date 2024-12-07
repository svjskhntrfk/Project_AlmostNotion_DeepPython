import starlette.status as status
from fastapi import APIRouter, Form, Depends
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext
from database import create_board, get_board_by_user_id_and_board_id, create_text, get_session

from database import *

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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
async def registration(email = Form(), username = Form(), password = Form(), password2 = Form(), session: AsyncSession = Depends(get_session)) :
    """
    Post-запрос, забираем данные пользователя с регистрации. Проверяем, что пользователь не был зарегистрирован ранее и совпадение повторного пароля с изначальным

    Параметры:
        email (Form): Почта пользователя
        username (Form): Имя пользователя
        password (Form): Пароль
        password2 (Form): Подтверждение пароля
        session (AsyncSession): Сессия в базе данных
    """
    user = await is_email_registered(email=email, session=session)
    if password == password2 and user == None :
        user_dict = {"email":email, "username":username, "password": get_password_hash(password), 'session': session}
    elif password != password2:
        return {"message" : "Passwords don't match"}
    else:
        return {"message": "This email is already registered"}

    await create_user(**user_dict)
    user = await is_email_registered(email=email, session=session)
    return RedirectResponse("/main_page/" + str(user.id),
                            status_code=status.HTTP_302_FOUND)

@router.post("/login")
async def login(email = Form(),password = Form(), session: AsyncSession = Depends(get_session)):
    """
    Авторизация пользователя

    Параметры:
        email (Form): Почта пользователя
        password (Form): Пароль пользователя
        session (AsyncSession): Сессия в базе данных
    """
    user = await is_email_registered(email=email, session=session)
    if not user:
        raise HTTPException(status_code=404, detail="Email not found")
    if not verify_password(password, user.password):
        raise HTTPException(status_code=404, detail="Wrong password")
    return RedirectResponse("/main_page/" + str(user.id),
        status_code=status.HTTP_302_FOUND)