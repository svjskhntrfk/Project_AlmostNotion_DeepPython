from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Security
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Annotated
from src.db import get_session, save_user_image
from src.schemas.image_schemas import ImageUploadResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth import check_access_token
from starlette.requests import Request
from src.db.cfg import settings
from src.db.utils.image_utils import get_images_by_user_id, delete_image

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
    session: AsyncSession = Depends(get_session)
) -> ImageUploadResponse:
    """
    Upload a user image with the following constraints:
    - Maximum file size: 5MB
    - Supported formats: jpg, jpeg, png, gif
    - File will be validated before upload
    """
    try:
        print(f"Uploading file: {file.filename}, size: {file.size}, content_type: {file.content_type}")
        if file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 5MB"
            )
        
        content_type = file.content_type
        if content_type not in ["image/jpeg", "image/png", "image/gif"]:
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Only JPEG, PNG and GIF are allowed"
            )

        user = request.state.user
        print(f"User ID: {user.id}")

        list_images = await get_images_by_user_id(user_id=user.id, session=session)
        if len(list_images) > 0:
            for image in list_images:
                await delete_image(image_id=image.id, session=session)
        
        image = await save_user_image(user_id=user.id, file=file, session=session)
        print(f"Image saved: {image.id}")
        
        image_url = image.url
        return ImageUploadResponse(
            id=image.id,
            file=image.file,
            url=image_url
        )
    except Exception as e:
        print(f"Error in upload_user_image: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
    

@router.get("/get-image-url/{image_id}")
async def get_image_url(image_id: str, session: AsyncSession = Depends(get_session)):
    url = await get_image_url(image_id, session)
    return {"url": url}

@router.get("/media/{file_path:path}")
async def get_media(file_path: str):
    """
    Получение медиа-файла из S3
    """
    url = f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET}/{file_path}"
    return RedirectResponse(url)