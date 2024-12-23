import asyncio
from typing import Type
import sqlalchemy
from fastapi import HTTPException, UploadFile
from sqlalchemy import UUID, Table, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import aliased
from backend.src.crud.base_crud import GenericCRUD
from models import Base
from models import Image
from image_schemas import ImageCreate, ImageUpdate, ImageDAOResponse
import uuid

class ImageDAO(GenericCRUD[Image, ImageCreate, ImageUpdate]):

    async def _get_image_url(self, db_obj: Image) -> ImageDAOResponse:
        """Получает url к экземпляру Image."""
        url = await db_obj.storage.generate_url(db_obj.file)
        return ImageDAOResponse(image=db_obj, url=url)

    async def get(
        self, *, id: UUID | str, scheme: bool = True, db_session: AsyncSession | None = None
    ) -> ImageDAOResponse | None:
        db_obj = await super().get(id=id, db_session=db_session)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Object not found")
        if scheme:
            image_with_url = await self._get_image_url(db_obj)
            return image_with_url
        url = await db_obj.storage.generate_url(db_obj.file)
        return db_obj, url

    async def create_with_file(
        self, *, file: UploadFile, model_instance: Base, path: str = "", db_session: AsyncSession | None = None
    ) -> Image | None:
        model_name, association_table_name = await self._check_association_table(
            model_instance=model_instance,
            related_model=self.model,
            db_session=db_session
        )


        db_obj = self.model(
            id=uuid.uuid4(),
            user_id=model_instance.id
        )
        db_obj.file = await db_obj.storage.put_object(file, path)
        db_session.add(db_obj)
        await db_session.flush()
        await db_session.refresh(db_obj)

        return db_obj
    

image_dao = ImageDAO(Image)