import starlette.status as status
from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse

from database1 import *

router = APIRouter(
    prefix="/board",
    tags=["Board"]
)
@router.post("/main_page/{user_id}/add_board")
async def registration(user_id: str) :
    board_id = await create_board(int(user_id))
    return RedirectResponse("/main_page/" + user_id + '/' + board_id ,
        status_code=status.HTTP_302_FOUND)

@router.post("/main_page/{user_id}/{board_id}/add_text")
async def registration(user_id: str, board_id: str, text = Form()) :
    await create_text(int(user_id), int(board_id), text)
    return RedirectResponse("/main_page/" + user_id + '/' + board_id ,
        status_code=status.HTTP_302_FOUND)