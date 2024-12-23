import asyncio
from typing import Type
import sqlalchemy
from fastapi import HTTPException, UploadFile
from sqlalchemy import UUID, Table, select, update
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import aliased
from src.backend.crud.base_crud import GenericCRUD
from src.db.models import Base
from src.db.models import Image, ImageBoard
from src.db.models import Board
from sqlalchemy.exc import SQLAlchemyError
import traceback
import logging
from src.schemas import ImageCreate, ImageUpdate, ImageDAOResponse
import uuid

logger = logging.getLogger(__name__)

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

class ImageBoardDAO(GenericCRUD[ImageBoard, ImageCreate, ImageUpdate]):
    def __init__(self, model):
        self.model = model

    async def _get_image_url(self, db_obj: ImageBoard) -> ImageDAOResponse:
        """Получает URL к экземпляру ImageBoard."""
        try:
            url = db_obj.url  # Предполагается, что URL генерируется через свойство url
            return ImageDAOResponse(image=db_obj, url=url)
        except Exception as e:
            logger.error(f"Error in _get_image_url: {str(e)}")
            traceback_str = traceback.format_exc()
            logger.error(f"Traceback: {traceback_str}")
            raise HTTPException(status_code=500, detail="Error occurred while generating image URL.")

    async def get(
        self, *, id: UUID | str, scheme: bool = True, db_session: AsyncSession
    ) -> ImageDAOResponse | tuple[ImageBoard, str]:
        """
        Получает изображение по ID. Если scheme=True, возвращает ImageDAOResponse с URL.
        Иначе возвращает кортеж с объектом ImageBoard и URL.
        """
        try:
            db_obj = await db_session.get(self.model, id)
            if not db_obj:
                logger.warning(f"ImageBoard with id {id} not found.")
                raise HTTPException(status_code=404, detail="Image not found")
            
            if scheme:
                image_with_url = await self._get_image_url(db_obj)
                return image_with_url
            
            url = db_obj.url
            return db_obj, url
        except HTTPException as e:
            logger.error(f"HTTPException in get: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in get: {str(e)}")
            traceback_str = traceback.format_exc()
            logger.error(f"Traceback: {traceback_str}")
            raise HTTPException(status_code=500, detail="Database error occurred while retrieving image.")
        except Exception as e:
            logger.error(f"Unexpected error in get: {str(e)}")
            traceback_str = traceback.format_exc()
            logger.error(f"Traceback: {traceback_str}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving the image.")

    async def create_with_file(
        self, *, file: UploadFile, board_instance: Board, path: str = "", db_session: AsyncSession
    ) -> ImageBoard:
        """
        Создаёт новое изображение с файлом и привязывает его к доске.
        
        :param file: Загружаемый файл
        :param board_instance: Экземпляр доски, к которой привязывается изображение
        :param path: Дополнительный путь для сохранения файла
        :param db_session: Асинхронная сессия SQLAlchemy
        :return: Созданный объект ImageBoard
        """
        try:
            new_image = self.model(
                id=uuid.uuid4(),
                board_id=board_instance.id
            )
            new_image.file = await new_image.storage.put_object(file, path)
            db_session.add(new_image)
            await db_session.flush()
            await db_session.refresh(new_image)
            logger.info(f"Created new ImageBoard with id {new_image.id} for board_id {board_instance.id}")
            return new_image
        except HTTPException as e:
            logger.error(f"HTTPException in create_with_file: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemyError in create_with_file: {str(e)}")
            traceback_str = traceback.format_exc()
            logger.error(f"Traceback: {traceback_str}")
            raise HTTPException(status_code=500, detail="Database error occurred while creating image.")
        except Exception as e:
            logger.error(f"Unexpected error in create_with_file: {str(e)}")
            traceback_str = traceback.format_exc()
            logger.error(f"Traceback: {traceback_str}")
            raise HTTPException(status_code=500, detail="An unexpected error occurred while creating the image.")

    # Дополнительно можно добавить методы для удаления и обновления изображений, если необходимо

# Создание экземпляра DAO
image_board_dao = ImageBoardDAO(ImageBoard)