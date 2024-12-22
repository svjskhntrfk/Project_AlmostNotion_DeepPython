from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Security
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Annotated
from database import get_session, save_user_image, get_images_by_user_id, delete_image
from image_schemas import ImageUploadResponse
from sqlalchemy.ext.asyncio import AsyncSession
from auth.middlewares.jwt.service import check_access_token
from starlette.requests import Request
from config import settings
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/image",
    tags=["Image"],
    dependencies=[Security(check_access_token)]
)

@router.post(
    "/upload-image",
    response_model=ImageUploadResponse,
    summary="Upload an image",
    description="Upload an image file with a flag indicating if it's the main image",
    responses={
        200: {
            "description": "Successfully uploaded image",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "file": "path/to/image.jpg",
                        "is_main": True,
                        "url": "http://minio.domain/media/path/to/image.jpg"
                    }
                }
            }
        },
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"}
    }
)
async def upload_user_image(
    request: Request,
    file: Annotated[UploadFile, File(description="Image file to upload")],
    is_main: Annotated[bool, Form(description="Flag indicating if this is the main image")],
    session: AsyncSession = Depends(get_session)
) -> ImageUploadResponse:
    """
    Upload a user image with size and format validation.
    """
    logger.info(f"Starting image upload process for file: {file.filename}")
    try:
        # Log file details
        logger.debug(f"File details - size: {file.size}, content_type: {file.content_type}")
        
        # Validate file size (5MB limit)
        if file.size > 5 * 1024 * 1024:
            logger.warning(f"File too large: {file.size} bytes")
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 5MB"
            )
        
        # Validate file type
        content_type = file.content_type
        if content_type not in ["image/jpeg", "image/png", "image/gif"]:
            logger.warning(f"Unsupported file type: {content_type}")
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Only JPEG, PNG and GIF are allowed"
            )

        user = request.state.user
        logger.debug(f"Processing upload for user_id: {user.id}")

        # Get existing images
        list_images = await get_images_by_user_id(user_id=user.id, session=session)
        logger.debug(f"Found {len(list_images)} existing images for user")

        # Delete existing images if any
        if len(list_images) > 0:
            logger.info("Deleting existing images")
            for image in list_images:
                logger.debug(f"Deleting image: {image.id}")
                await delete_image(image_id=image.id, session=session)
        
        # Save new image
        logger.info("Saving new image")
        image = await save_user_image(user_id=user.id, file=file, is_main=is_main, session=session)
        logger.info(f"Successfully saved image with id: {image.id}")
        
        image_url = image.url
        logger.debug(f"Generated image URL: {image_url}")

        return ImageUploadResponse(
            id=image.id,
            file=image.file,
            is_main=True,
            url=image_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_user_image: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error") from e

@router.get("/get-image-url/{image_id}")
async def get_image_url(image_id: str, session: AsyncSession = Depends(get_session)):
    """
    Get the URL for a specific image.
    """
    logger.info(f"Getting URL for image_id: {image_id}")
    try:
        url = await get_image_url(image_id, session)
        logger.debug(f"Generated URL: {url}")
        return {"url": url}
    except Exception as e:
        logger.error(f"Error getting image URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get image URL")

@router.get("/media/{file_path:path}")
async def get_media(file_path: str):
    """
    Get media file from MinIO storage.
    """
    logger.info(f"Accessing media file: {file_path}")
    try:
        url = f"http://{settings.MINIO_DOMAIN}/{settings.MINIO_MEDIA_BUCKET}/{file_path}"
        logger.debug(f"Generated MinIO URL: {url}")
        return RedirectResponse(url)
    except Exception as e:
        logger.error(f"Error accessing media file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to access media file")


