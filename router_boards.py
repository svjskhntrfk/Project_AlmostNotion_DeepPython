import starlette.status as status
from fastapi import APIRouter, Form, Body
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates
from typing import Dict

from database1 import *


templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/board",
    tags=["Board"]
)
@router.get("/main_page/{user_id}/add_board")
async def create_new_board(user_id: str) :
    board_id = await create_board(int(user_id), "board1")
    return RedirectResponse("/board/main_page/" + user_id + '/' + str(board_id) ,
        status_code=status.HTTP_302_FOUND)

@router.get("/main_page/{user_id}/{board_id}")
async def board_page(user_id: str, board_id: str, request: Request):
    board = await get_board_by_user_id_and_board_id(int(user_id), int(board_id))
    print(board)
    return templates.TemplateResponse("article.html", {"request": request, "user_id": user_id, "board_id":board_id, "texts" : board["texts"]})


@router.post("/main_page/{user_id}/{board_id}/add_text")
async def add_text_on_board(
    user_id: str, 
    board_id: str, 
    data: Dict = Body(...)
):
    text = data.get("text")
    text_id = await create_text(int(board_id), text)
    return {"text_id": text_id}

@router.post("/main_page/{user_id}/{board_id}/update_text")
async def update_text_on_board(
    user_id: str, 
    board_id: str, 
    data: Dict = Body(...)
):
    text_id = data.get("text_id")
    new_text = data.get("text")
    
    async with async_session_maker() as session:
        async with session.begin():
            query = select(Board).filter(Board.id == int(board_id))
            result = await session.execute(query)
            board = result.scalars().first()
            
            if not board:
                raise HTTPException(status_code=404, detail="Board not found")
            
            content = dict(board.content)
            for text in content["texts"]:
                if text["id"] == text_id:
                    text["text"] = new_text
                    break
            
            board.content = content
            await session.flush()
    
    return {"status": "success"}