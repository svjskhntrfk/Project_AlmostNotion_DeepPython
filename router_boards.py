import starlette.status as status
from fastapi import APIRouter, Form, Body, Depends
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.responses import RedirectResponse
from starlette import status
from database import create_board, get_board_by_user_id_and_board_id, create_text, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from typing import Dict


from database import *

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/board",
    tags=["Board"]
)

@router.post("/main_page/{user_id}/add_board")
async def create_new_board(user_id: str, boardName = Form(), session: AsyncSession = Depends(get_session)):
    """
    Создает новую доску для пользователя.

    Параметры:
        user_id (str): ID пользователя, который создает доску
        boardName (Form): имя доски
        session (AsyncSession): Сессия в базе данных
    """
    board_id = await create_board(int(user_id), boardName, session)
    return RedirectResponse(
        f"/board/main_page/{user_id}/{board_id}",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/main_page/{user_id}/{board_id}")
async def board_page(user_id: str, board_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    """
    Get-запрос, переходит на доску

    Параметры:
        user_id (str): ID пользователя
        board_id (str): ID доски
        request (Request): Исходящий запрос с сервера
        session (AsyncSession): Сессия в базе данных
    """
    board = await get_board_by_user_id_and_board_id(int(user_id), int(board_id), session)
    user = await get_user_by_id(int(user_id), session)
    return templates.TemplateResponse(
        "article.html",
        {
            "request": request,
            "user_id": user_id,
            "board_id": board_id,
            "texts": board[1]["texts"],
            "username" : user.username,
            "title" : board[0]
        }
    )

@router.post("/main_page/{user_id}/{board_id}/add_text")
async def add_text_on_board(
    user_id: str,
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

@router.post("/main_page/{user_id}/{board_id}/update_text")
async def update_text_on_board(
    user_id: str,
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
