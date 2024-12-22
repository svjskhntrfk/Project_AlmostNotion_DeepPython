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
import logging

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/board",
    tags=["Board"],
    dependencies=[Security(check_access_token)]
)

@router.post("/main_page/add_board")
async def create_new_board(request: Request, boardName = Form(), session: AsyncSession = Depends(get_session)):
    """Creates a new board for the user."""
    logger.info(f"Creating new board: {boardName}")
    try:
        user = request.state.user
        logger.debug(f"Creating board for user_id: {user.id}")
        
        board_id = await create_board(int(user.id), boardName, session)
        logger.info(f"Successfully created board with id: {board_id}")
        
        return RedirectResponse(
            f"/board/main_page/{board_id}",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"Error creating board: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create board")

@router.get("/main_page/{board_id}")
async def board_page(board_id: str, request: Request, session: AsyncSession = Depends(get_session)):
    """Get request for board page."""
    logger.info(f"Accessing board page for board_id: {board_id}")
    try:
        user = request.state.user
        logger.debug(f"Fetching board for user_id: {user.id}, board_id: {board_id}")
        
        board = await get_board_by_user_id_and_board_id(int(user.id), int(board_id), session)
        user_images = await get_images_by_user_id(user.id, session=session)
        
        image_url = None
        if user_images:
            latest_image = user_images[-1]
            image_url = latest_image.url
            logger.debug(f"Using latest image URL: {image_url}")
        
        logger.info(f"Successfully retrieved board page for board_id: {board_id}")
        return templates.TemplateResponse(
            "article.html",
            {
                "request": request,
                "user_id": user.id,
                "board_id": board_id,
                "texts": board[1]["texts"],
                "username": user.username,
                "title": board[0],
                "image_url": image_url
            }
        )
    except Exception as e:
        logger.error(f"Error accessing board page: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load board page")

@router.post("/main_page/{board_id}/add_text")
async def add_text_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Adds text to the current board."""
    logger.info(f"Adding text to board_id: {board_id}")
    try:
        text = data.get("text")
        logger.debug(f"Adding text: {text[:50]}...")  # Log first 50 chars of text
        
        text_id = await create_text(int(board_id), text, session)
        logger.info(f"Successfully added text with id: {text_id} to board: {board_id}")
        
        return {"text_id": text_id}
    except Exception as e:
        logger.error(f"Error adding text to board: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add text")

@router.post("/main_page/{board_id}/update_text")
async def update_text_on_board(
    board_id: str,
    data: Dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    """Updates text on the board."""
    logger.info(f"Updating text on board_id: {board_id}")
    try:
        text_id = data.get("text_id")
        new_text = data.get("text")
        logger.debug(f"Updating text_id: {text_id} with new text: {new_text[:50]}...")
        
        await update_text(int(board_id), text_id, new_text, session)
        logger.info(f"Successfully updated text_id: {text_id} on board: {board_id}")
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating text: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update text")

@router.post("/main_page/{board_id}/add_collaborator")
async def add_board_collaborator(
    board_id: str, 
    email_collaborator = Form(), 
    session: AsyncSession = Depends(get_session)
):
    """Adds a collaborator to the board."""
    logger.info(f"Adding collaborator with email: {email_collaborator} to board_id: {board_id}")
    try:
        new_collaborator = await is_email_registered(str(email_collaborator), session)
        if not new_collaborator:
            logger.warning(f"Collaborator email not found: {email_collaborator}")
            raise HTTPException(status_code=404, detail="User not found")
            
        logger.debug(f"Adding user_id: {new_collaborator.id} as collaborator")
        await add_collaborator(int(new_collaborator.id), int(board_id), session)
        logger.info(f"Successfully added collaborator to board: {board_id}")
        
        return {'status': 'success'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding collaborator: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add collaborator")