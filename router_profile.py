import starlette.status as status
from fastapi import APIRouter, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse
from passlib.context import CryptContext

from database import *

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
@router.post("/main_page/profile/{user_id}/change_name")
async def profile_page(user_id : str, first_name = Form(), session: AsyncSession = Depends(get_session)) :
    await change_username(int(user_id), first_name, session=session)
    return RedirectResponse("/profile/main_page/profile/" + str(user_id),
                            status_code=status.HTTP_302_FOUND)

@router.post("/main_page/profile/{user_id}/change_password")
async def profile_page(user_id : str, old_password = Form(), new_password = Form(), session: AsyncSession = Depends(get_session)) :
    user = await get_user_by_id(int(user_id), session)
    if verify_password(old_password, user.password):
        await change_password(int(user_id), get_password_hash(new_password), session=session)
    return RedirectResponse("/profile/main_page/profile/" + str(user_id),
                            status_code=status.HTTP_302_FOUND)

@router.get("/main_page/profile/{user_id}", response_class=HTMLResponse)
async def profile_page(user_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    user = await get_user_by_id(int(user_id), session=session)
    return templates.TemplateResponse("profile.html", {"request": request, "user_id" : user_id, "username": user.username })
