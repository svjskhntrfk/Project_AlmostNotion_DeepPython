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
import logging

logger = logging.getLogger(__name__)

class ImageDAO(GenericCRUD[Image, ImageCreate, ImageUpdate]):
    async def _reset_is_main(self, model_name: str, model_instance: Base, association_table_name: str, db_session: AsyncSession):
        """Resets is_main value for all images associated with the model."""
        logger.debug(f"Resetting is_main for {model_name} with id: {model_instance.id}")
        try:
            association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
            image_alias = aliased(Image)
            stmt = (
                select(image_alias.id)
                .select_from(association_table)
                .join(image_alias, association_table.c["image_id"] == image_alias.id)
                .where(association_table.c[f"{model_name}_id"] == model_instance.id)
                .where(image_alias.is_main == True)  # noqa: E712
            )
            result = await db_session.execute(stmt)
            image_ids = [row[0] for row in result.fetchall()]
            
            if image_ids:
                logger.debug(f"Found {len(image_ids)} main images to reset")
                stmt = (
                    update(Image)
                    .where(Image.id.in_(image_ids))
                    .values(is_main=False)
                )
                await db_session.execute(stmt)
                await db_session.commit()
                logger.info(f"Successfully reset is_main for {len(image_ids)} images")
        except Exception as e:
            logger.error(f"Error resetting is_main: {str(e)}")
            raise

    async def _get_image_url(self, db_obj: Image) -> ImageDAOResponse:
        """Gets url for Image instance."""
        logger.debug(f"Generating URL for image: {db_obj.id}")
        try:
            url = await db_obj.storage.generate_url(db_obj.file)
            logger.debug(f"Generated URL for image {db_obj.id}: {url}")
            return ImageDAOResponse(image=db_obj, url=url)
        except Exception as e:
            logger.error(f"Error generating URL for image {db_obj.id}: {str(e)}")
            raise

    async def get(
        self, *, id: UUID | str, scheme: bool = True, db_session: AsyncSession | None = None
    ) -> ImageDAOResponse | None:
        logger.debug(f"Getting image with id: {id}, scheme: {scheme}")
        try:
            db_obj = await super().get(id=id, db_session=db_session)
            if not db_obj:
                logger.warning(f"Image not found with id: {id}")
                raise HTTPException(status_code=404, detail="Object not found")
            
            if scheme:
                logger.debug(f"Retrieving image with URL for id: {id}")
                image_with_url = await self._get_image_url(db_obj)
                return image_with_url
            
            url = await db_obj.storage.generate_url(db_obj.file)
            logger.debug(f"Retrieved image {id} with URL: {url}")
            return db_obj, url
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving image {id}: {str(e)}")
            raise

    async def create_with_file(
        self, *, file: UploadFile, is_main: bool, model_instance: Base, path: str = "", db_session: AsyncSession | None = None
    ) -> Image | None:
        logger.info(f"Creating new image with file: {file.filename}, is_main: {is_main}")
        try:
            model_name, association_table_name = await self._check_association_table(
                model_instance=model_instance,
                related_model=self.model,
                db_session=db_session
            )
            logger.debug(f"Checked association table: {association_table_name}")

            if is_main:
                logger.debug("Resetting existing main images")
                await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

            db_obj = self.model(
                id=uuid.uuid4(),
                is_main=is_main,
                user_id=model_instance.id
            )
            logger.debug(f"Created image object with id: {db_obj.id}")

            db_obj.file = await db_obj.storage.put_object(file, path)
            logger.debug(f"Uploaded file to storage: {db_obj.file}")

            db_session.add(db_obj)
            await db_session.flush()
            await db_session.refresh(db_obj)
            
            logger.info(f"Successfully created image with id: {db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"Error creating image with file {file.filename}: {str(e)}")
            raise

image_dao = ImageDAO(Image)
logger.info("Initialized ImageDAO")