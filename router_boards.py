import starlette.status as status
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

from database1 import *

router = APIRouter(
    prefix="/board",
    tags=["Board"]
)
@router.get("/main_page/{user_id}/add_board")
async def create_new_board(user_id: str) :
    board_id = await create_board(int(user_id))
    return RedirectResponse("/main_page/" + user_id + '/' + board_id ,
        status_code=status.HTTP_302_FOUND)

@router.post("/main_page/{user_id}/{board_id}/add_text")
async def add_text_on_board(user_id: str, board_id: str, text = Form()) :
    await create_text(int(user_id), board_id, text)
    return RedirectResponse("/main_page/" + user_id + '/' + board_id ,
        status_code=status.HTTP_302_FOUND)