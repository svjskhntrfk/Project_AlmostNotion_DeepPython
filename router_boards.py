import starlette.status as status
from fastapi import APIRouter, Form, Body, Depends, Security
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.responses import RedirectResponse
from starlette import status
from database import create_board, get_board_by_user_id_and_board_id, create_text, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from typing import Dict
from auth.middlewares.jwt.service import check_access_token

from database import *

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/board",
    tags=["Board"],
    dependencies=[Security(check_access_token)]
)

@router.post("/main_page/add_board")
async def create_new_board(request: Request, boardName = Form(), session: AsyncSession = Depends(get_session)):
    """
    Создает новую доску для пользователя.

    Параметры:
        user_id (str): ID пользователя, который создает доску
        boardName (Form): имя доски
        session (AsyncSession): Сессия в базе данных
    """
    user = request.state.user
    board_id = await create_board(int(user.id), boardName, session)
    return RedirectResponse(
        f"/board/main_page/{board_id}",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/main_page/{board_id}")
async def board_page(board_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    """
    Get-запрос, переходит на доску

    Параметры:
        user_id (str): ID пользователя
        board_id (str): ID доски
        request (Request): Исходящий запрос с сервера
        session (AsyncSession): Сессия в базе данных
    """
    user = request.state.user
    board = await get_board_by_user_id_and_board_id(int(user.id), int(board_id), session)
    user_images = await get_images_by_user_id(user.id, session=session)
    
    # Получаем URL последнего изображения
    image_url = None
    print(user_images)
    if user_images:
        latest_image = user_images[-1]
        # Используем свойство url из ImageSchema
        image_url = latest_image.url
    
    board_images = await get_images_by_board_id(int(board_id), session=session)
    images_url = [image.url for image in board_images]
    print(images_url)
    return templates.TemplateResponse(
        "article.html",
        {
            "request": request,
            "user_id": user.id,
            "board_id": board_id,
            "texts": board[1]["texts"],
            "username" : user.username,
            "title" : board[0],
            "image_url" : image_url,
            "board_images" : images_url
        }
    )

@router.post("/main_page/{board_id}/add_text")
async def add_text_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Добавляет текст на текущую доску

    Параметры:
        user_id (str): ID пользователя
        board_id (str): ID текущей доски
        data (Dict): текст, который вводит пользователь
        session (AsyncSession): Сессия в базе данных
    """
    text = data.get("text")
    text_id = await create_text(int(board_id), text, session)
    return {"text_id": text_id}

@router.post("/main_page/{board_id}/update_text")
async def update_text_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Обновление текста на доске

    Параметры:
        user_id (str): ID пользователя
        board_id (str): ID текущей доски
        data (Dict): Текст и его ID
        session (AsyncSession): Сессия в базе данных
    """

    text_id = data.get("text_id")
    new_text = data.get("text")
    await update_text(int(board_id), text_id, new_text,session)
    return {"status": "success"}

@router.post("/main_page/{board_id}/add_collaborator")
async def add_board_collaborator( board_id: str, email_collaborator = Form(), session: AsyncSession = Depends(get_session)):
    new_collaborator = await is_email_registered(str(email_collaborator), session)
    await add_collaborator(int(new_collaborator.id), int(board_id), session)
    return {'status': 'success'}

@router.post("/main_page/{board_id}/add_image")
async def add_image_on_board(board_id: str, file: UploadFile, session: AsyncSession = Depends(get_session)):
    await save_image_on_board(int(board_id), file, session)
    return {'status': 'success'}    