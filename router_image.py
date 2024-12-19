from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Security
from fastapi.responses import JSONResponse
from typing import Annotated
from database import get_session, save_user_image
from image_schemas import ImageUploadResponse
from sqlalchemy.ext.asyncio import AsyncSession
from auth.middlewares.jwt.service import check_access_token
from starlette.requests import Request

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
    Upload a user image with the following constraints:
    - Maximum file size: 5MB
    - Supported formats: jpg, jpeg, png, gif
    - File will be validated before upload
    """
    # Validate file size (5MB limit)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 5MB"
        )
    
    # Validate file type
    content_type = file.content_type
    if content_type not in ["image/jpeg", "image/png", "image/gif"]:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type. Only JPEG, PNG and GIF are allowed"
        )

    user = request.state.user
    image = await save_user_image(user_id=user.id, file=file, is_main=is_main, session=session)
    
    # Construct the full URL for the image
    image_url = f"http://{request.base_url.netloc}/media/{image.file}"
    
    return ImageUploadResponse(
        id=image.id,
        file=image.file,
        is_main=image.is_main,
        url=image_url
    )