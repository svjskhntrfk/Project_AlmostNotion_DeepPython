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
import time
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
    board = await get_board_with_todo_lists(int(board_id), session)
    user_images = await get_images_by_user_id(user.id, session=session)
    
    # Получаем URL последнего изображения
    image_url = None
    print(user_images)
    if user_images:
        latest_image = user_images[-1]
        # Используем свойство url из ImageSchema
        image_url = latest_image.url
    return templates.TemplateResponse(
        "article.html",
        {
            "request": request,
            "user_id": user.id,
            "board_id": board_id,
            "texts": board.content["texts"],
            "todo_lists": board.todo_lists,
            "username" : user.username,
            "title" : board.title,
            "image_url" : image_url
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

@router.post("/main_page/{board_id}/add_to_do_list")
async def add_todo_list_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Добавляет to do список на текущую доску

    Параметры:
        user_id (str): ID пользователя
        board_id (str): ID текущей доски
        data (Dict): текст, который вводит пользователь
        session (AsyncSession): Сессия в базе данных
    """
    title = data.get("title")
    print('title', title)
    text = data.get("text")
    print('text', text)
    to_do_list_id = await create_todo_list(int(board_id), title,None, session)
    print('to_do_list_id', to_do_list_id)
    to_do_list_new_item = await create_task(to_do_list_id, text, None, session)
    print('to_do_list_new_item', to_do_list_new_item)
    return {"to_do_list_id": to_do_list_id, "to_do_list_new_item" : to_do_list_new_item }

@router.post("/main_page/{board_id}/add_to_do_list_item")
async def add_todo_list_item_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Добавляет to do список на текущую доску

    Параметры:
        user_id (str): ID пользователя
        board_id (str): ID текущей доски
        data (Dict): текст, который вводит пользователь
        session (AsyncSession): Сессия в базе данных
    """
    text = data.get("text")
    to_do_list_id = data.get("to_do_list_id")
    to_do_list_new_item = await create_task(int(to_do_list_id), text, deadline=None, session=session)
    return {"to_do_list_id": to_do_list_id, "to_do_list_new_item" : to_do_list_new_item }

@router.post("/main_page/{board_id}/update_to_do_list_item")
async def update_todo_list_item(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Updates a todo list item's completion status
    """
    task_id = data.get("to_do_list_item_id")
    completed = data.get("completed")
    text = data.get("text")
    
    await update_task(
        task_id=int(task_id),
        new_title=text,
        completed=completed,
        new_deadline=None,
        session=session
    )
    return {"status": "success"}

@router.post("/main_page/{board_id}/update_to_do_list_title")
async def update_todo_list_title_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Добавляет to do список на текущую доску

    Параметры:
        user_id (str): ID пользователя      
        board_id (str): ID текущей доски
        data (Dict): текст, который вводит пользователь
        session (AsyncSession): Сессия в базе данных
    """
    title = data.get("title")
    to_do_list_id = data.get("to_do_list_id")
    await update_todo_list(int(to_do_list_id), title, None,  session)
    return {"status": "success"}

@router.post("/main_page/{board_id}/delete_to_do_list")
async def delete_todo_list_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    to_do_list_id = data.get("to_do_list_id")
    await delete_todo_list(int(to_do_list_id), session)
    return {"status": "success"}

@router.post("/main_page/{board_id}/update_to_do_list")
async def update_todo_list(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Updates a todo list's title
    """
    todo_list_id = data.get("to_do_list_id")
    title = data.get("title")
    
    await update_todo_list(
        todo_list_id=int(todo_list_id),
        new_title=title,
        new_deadline=None,
        session=session
    )
    return {"status": "success"}

@router.post("/main_page/{board_id}/add_collaborator")
async def add_board_collaborator( board_id: str, email_collaborator = Form(), session: AsyncSession = Depends(get_session)):
    new_collaborator = await is_email_registered(str(email_collaborator), session)
    await add_collaborator(int(new_collaborator.id), int(board_id), session)
    return {'status': 'success'}

