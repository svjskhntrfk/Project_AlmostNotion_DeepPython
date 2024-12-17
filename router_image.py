from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from pydantic import UUID4
from backend.src.crud.user_crud import UserManager, get_current_active_user_and_manager
from image_schemas import (ImageDAOResponse, UploadImageResponse, UploadUrlImageResponse)
from starlette import status
import filetype

account_router = APIRouter()

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_file(file: UploadFile):
    # Проверка на размер файла
    if file.size > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Uploaded file exceeds size limit of 5MB.")

    # Проверка на тип файла
    kind = filetype.guess(file.file.read(1024))  # Чтение первых 1024 байт файла для определения типа
    if kind is None or kind.mime.split('/')[0] != 'image':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid file type. Only image files are allowed.")

    file.file.seek(0)  # Сброс указателя файла после чтения

@account_router.post("/upload-image", response_model=UploadImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_image(
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image = await user_manager.save_user_image(file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)

@account_router.put("/update-image/{image_id}", response_model=UploadImageResponse, status_code=status.HTTP_200_OK)
async def update_user_image(
    image_id: UUID4,
    file: UploadFile = File(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image = await user_manager.update_user_image(image_id=image_id, file=file, is_main=is_main)
    return UploadImageResponse(id=image.id, file=image.file, is_main=image.is_main)

@account_router.delete("/delete-image/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_image(
    image_id: UUID4,
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    await user_manager.delete_user_image(image_id=image_id)
    return {"detail": "Image deleted successfully"}

@account_router.post("/upload-url-image", response_model=UploadUrlImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_user_image_with_url(
    file_name: str = Form(...),
    is_main: bool = Form(...),
    front_key: str = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image_dao_resp = await user_manager.save_user_image_with_upload_url(file_name, is_main=is_main)
    return UploadUrlImageResponse(image=image_dao_resp, front_key=front_key)

@account_router.post("/update-url-image/{image_id}", response_model=ImageDAOResponse, status_code=status.HTTP_201_CREATED)
async def update_user_image_with_url(
    image_id: UUID4,
    file_name: str = Form(...),
    is_main: bool = Form(...),
    user_manager: UserManager = Depends(get_current_active_user_and_manager)
):
    image_dao_resp = await user_manager.update_user_image_with_upload_url(image_id, file_name, is_main)
    return image_dao_resp