import uuid
from typing import List, Optional, Tuple

from fastapi import Depends, Request, UploadFile
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (AuthenticationBackend,
                                          BearerTransport, JWTStrategy)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserAlreadyExists
from sqlalchemy import UUID, String, cast
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.src.conf.logging import logger
from config import settings
from backend.src.crud.image_crud import image_dao
from src.db.deps import get_user_db
from models import Image, User
from src.schemas.user_schema import UserCreate

logger = logger.getChild(__name__)

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY
    image_path = "users"

    def __init__(self, user_db: SQLAlchemyUserDatabase, user: Optional[User] = None):
        super().__init__(user_db)
        self.user = user

    @property
    def db_session(self):
        return self.user_db.session

    async def save_user_image(self, file: UploadFile, is_main: bool) -> Image:
        image = await image_dao.create_with_file(
            file=file, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session
        )
        return image

    async def update_user_image(self, image_id: uuid.UUID, file: UploadFile, is_main: bool) -> Image:
        image = await image_dao.update_file(id=image_id, file=file, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session)
        return image

    async def delete_user_image(self, image_id: uuid.UUID) -> None:
        await image_dao.delete(
            id=image_id, model_instance=self.user, related_model=Image, db_session=self.db_session
        )

    async def save_user_image_with_upload_url(self, file_name: str, is_main: bool) -> str:
        image_dao_resp = await image_dao.create_without_file(
            is_main=is_main, file_name=file_name, model_instance=self.user, path=self.image_path, db_session=self.db_session
        )
        return image_dao_resp

    async def update_user_image_with_upload_url(self, image_id: uuid.UUID, file_name: str, is_main: bool) -> str:
        image_dao_resp = await image_dao.update_without_file(
            id=image_id, file_name=file_name, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session
        )
        return image_dao_resp