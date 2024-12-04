import starlette.status as status
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from fastapi.templating import Jinja2Templates

from database1 import *


templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/board",
    tags=["Board"]
)
@router.post("/main_page/{user_id}/add_board")
async def create_new_board(user_id: str, title = Form()) :
    board_id = await create_board(int(user_id), str(title))
    return RedirectResponse("/board/main_page/" + user_id + '/' + str(board_id) ,
        status_code=status.HTTP_302_FOUND)

@router.get("/main_page/{user_id}/add_board")
async def board_title_page(user_id: str, request: Request):
    return templates.TemplateResponse("board_title.html", {"request": request, "user_id": user_id})


@router.get("/main_page/{user_id}/{board_id}")
async def board_page(user_id: str, board_id: str, request: Request):
    board = await get_board_by_user_id_and_board_id(int(user_id), int(board_id))
    print(board)
    return templates.TemplateResponse("article.html", {"request": request, "user_id": user_id, "board_id":board_id, "texts" : board["texts"]})


@router.post("/main_page/{user_id}/{board_id}/add_text")
async def add_text_on_board(user_id: str, board_id: str, text = Form()) :
    text_id = await create_text(int(board_id), text)
    print(text_id)
    return RedirectResponse("/board/main_page/" + user_id + '/' + board_id ,
        status_code=status.HTTP_302_FOUND)

@router.get("/main_page/{user_id}/add_board/add_text")
async def board_text_page(request: Request):
    return templates.TemplateResponse("article.html", {"request": request})
