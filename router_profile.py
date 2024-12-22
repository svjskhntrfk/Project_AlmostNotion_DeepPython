import starlette.status as status
from fastapi import APIRouter, Form, Depends, Security
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from passlib.context import CryptContext
from auth.middlewares.jwt.service import check_access_token
from hashlib import sha256
from database import *
from auth.service import AuthService
from auth.middlewares.jwt.base.auth import JWTAuth
from auth.jwt_settings import jwt_config

def get_auth_service() -> AuthService:
    return AuthService(jwt_auth=JWTAuth(config=jwt_config))

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
    dependencies=[Security(check_access_token)]
)

def get_sha256_hash(line: str) -> str:
    return sha256(str.encode(line)).hexdigest()


@router.get("/main_page", response_class=HTMLResponse)
async def main_page(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Отображает главную страницу пользователя с его досками.

    Параметры:
        user_id (str): ID пользователя
        request (Request): Объект HTTP-запроса
        session (AsyncSession): Сессия в базе данных
    """
    print("Request state:", request.state.__dict__) 
    user = request.state.user
    user_id = user.id
    boards_id_and_names = await get_boards_by_user_id(int(user_id), session=session)
    context = []
    for board in boards_id_and_names:
        context.append({"url":"/board/main_page/" + str(board["id"]), "name": board["title"]})
    user_images = await get_images_by_user_id(user.id, session=session)
    
    # Получаем URL последнего изображения
    image_url = None
    print(user_images)
    if user_images:
        latest_image = user_images[-1]
        # Используем свойство url из ImageSchema
        image_url = latest_image.url
    return templates.TemplateResponse("main_page.html", {"request": request, "username": user.username, "links" : context, "image_url": image_url})

@router.post("/main_page/profile/change_name")
async def profile_page_change_name(request: Request, first_name = Form(), session: AsyncSession = Depends(get_session)) :
    user = request.state.user
    user_id = user.id
    await change_username(int(user_id), first_name, session=session)
    return RedirectResponse("/profile/main_page/profile/",
                            status_code=status.HTTP_302_FOUND)

@router.post("/main_page/profile/change_password")
async def profile_page_change_password(request: Request, old_password = Form(), new_password = Form(), session: AsyncSession = Depends(get_session)) :
    user = request.state.user
    user_id = user.id
    if user.password == get_sha256_hash(old_password):
        await change_password(int(user_id), get_sha256_hash(new_password), session=session)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текущий пароль введен неверно!")
    return RedirectResponse("/login",
                            status_code=status.HTTP_302_FOUND)

@router.get("/main_page/profile", response_class=HTMLResponse)
async def profile_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = request.state.user
    
    # Получаем основное изображение пользователя
    user_images = await get_images_by_user_id(user.id, session=session)
    
    # Получаем URL последнего изображения
    image_url = None
    print(user_images)
    if user_images:
        latest_image = user_images[-1]
        # Используем свойство url из ImageSchema
        image_url = latest_image.url
    
    print(f"Image URL: {image_url}")  # Для отладки
    
    return templates.TemplateResponse(
        "profile.html", 
        {
            "request": request, 
            "username": user.username,
            "image_url": image_url
        }
    )

@router.get("/logout")
async def logout(request: Request, session: AsyncSession = Depends(get_session),auth_service: AuthService = Depends(get_auth_service)   ):
    user = request.state.user
    device_id = request.state.device_id
    await auth_service.logout(user, device_id, session=session)
    return RedirectResponse("/",
                            status_code=status.HTTP_302_FOUND)
