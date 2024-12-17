from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from pydantic import UUID4
from database import *
from image_schemas import (ImageDAOResponse, UploadImageResponse, UploadUrlImageResponse)
from starlette import status
import filetype

router = APIRouter(
    prefix="/image",
    tags=["Image"]
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
    file: UploadFile = File(...),
    is_main: bool = Form(...)
):
    image = await save_user_image(file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)

