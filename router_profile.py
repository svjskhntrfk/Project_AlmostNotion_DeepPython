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
import logging

logger = logging.getLogger(__name__)


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
    Displays the user's main page with their boards.
    """
    logger.info("Accessing main page")
    try:
        user = request.state.user
        logger.debug(f"Loading main page for user_id: {user.id}")

        boards_id_and_names = await get_boards_by_user_id(int(user.id), session=session)
        logger.debug(f"Retrieved {len(boards_id_and_names)} boards for user")

        context = []
        for board in boards_id_and_names:
            context.append({"url": f"/board/main_page/{board['id']}", "name": board["title"]})

        user_images = await get_images_by_user_id(user.id, session=session)
        logger.debug(f"Retrieved {len(user_images) if user_images else 0} images for user")

        image_url = None
        if user_images:
            latest_image = user_images[-1]
            image_url = latest_image.url
            logger.debug(f"Using latest image URL: {image_url}")

        logger.info(f"Successfully loaded main page for user: {user.username}")
        return templates.TemplateResponse(
            "main_page.html",
            {
                "request": request,
                "username": user.username,
                "links": context,
                "image_url": image_url
            }
        )
    except Exception as e:
        logger.error(f"Error loading main page: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load main page")


@router.post("/main_page/profile/change_name")
async def profile_page_change_name(request: Request, first_name=Form(), session: AsyncSession = Depends(get_session)):
    """
    Changes the user's username.
    """
    logger.info("Processing username change request")
    try:
        user = request.state.user
        logger.debug(f"Changing username for user_id: {user.id} to: {first_name}")

        await change_username(int(user.id), first_name, session=session)
        logger.info(f"Successfully changed username for user_id: {user.id}")

        return RedirectResponse(
            "/profile/main_page/profile/",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        logger.error(f"Error changing username: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change username")


@router.post("/main_page/profile/change_password")
async def profile_page_change_password(
    request: Request,
    old_password=Form(),
    new_password=Form(),
    session: AsyncSession = Depends(get_session)
):
    """
    Changes the user's password.
    """
    logger.info("Processing password change request")
    try:
        user = request.state.user
        logger.debug(f"Attempting password change for user_id: {user.id}")

        if user.password == get_sha256_hash(old_password):
            await change_password(int(user.id), get_sha256_hash(new_password), session=session)
            logger.info(f"Successfully changed password for user_id: {user.id}")
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        else:
            logger.warning(f"Invalid old password provided for user_id: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Текущий пароль введен неверно!"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.get("/main_page/profile", response_class=HTMLResponse)
async def profile_page(request: Request, session: AsyncSession = Depends(get_session)):
    """
    Displays the user's profile page.
    """
    logger.info("Accessing profile page")
    try:
        user = request.state.user
        logger.debug(f"Loading profile page for user_id: {user.id}")

        user_images = await get_images_by_user_id(user.id, session=session)
        logger.debug(f"Retrieved {len(user_images) if user_images else 0} images for user")

        image_url = None
        if user_images:
            latest_image = user_images[-1]
            image_url = latest_image.url
            logger.debug(f"Using latest image URL: {image_url}")

        logger.info(f"Successfully loaded profile page for user: {user.username}")
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "username": user.username,
                "image_url": image_url
            }
        )
    except Exception as e:
        logger.error(f"Error loading profile page: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load profile page")


@router.get("/logout")
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_session),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logs out the user.
    """
    logger.info("Processing logout request")
    try:
        user = request.state.user
        device_id = request.state.device_id
        logger.debug(f"Logging out user_id: {user.id} from device: {device_id}")

        await auth_service.logout(user, device_id, session=session)
        logger.info(f"Successfully logged out user_id: {user.id}")

        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        # Still redirect to home page even if there's an error
        return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

