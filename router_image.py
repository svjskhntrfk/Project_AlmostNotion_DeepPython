from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Security
from pydantic import UUID4
from database import *
from image_schemas import (ImageDAOResponse, UploadImageResponse, UploadUrlImageResponse)
from starlette import status
import filetype
from auth.middlewares.jwt.service import check_access_token
from starlette.requests import Request

router = APIRouter(
    prefix="/image",
    tags=["Image"],
    dependencies=[Security(check_access_token)]
)

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

def validate_image_file(file: UploadFile):
    if file.size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Uploaded file exceeds size limit of 5MB.")

    kind = filetype.guess(file.file.read(1024))
    if kind is None or kind.mime.split('/')[0] != 'image':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Only image files are allowed.")

    file.file.seek(0)

@router.post("/upload-image")
async def upload_user_image(
    request : Request,
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    session: AsyncSession = Depends(get_session)
):
    user = request.state.user
    image = await save_user_image(user_id=user.id, file=file, is_main=is_main, session=session)
    return UploadImageResponse(id=uuid.UUID(str(image.id)), is_main=image.is_main)

