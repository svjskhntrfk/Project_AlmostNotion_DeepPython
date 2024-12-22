from typing import Any, Generic, List, Type, TypeVar, Sequence
from uuid import UUID

from fastapi import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import exc, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import selectinload
from models import Base

import logging

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)
T = TypeVar("T", bound=Base)


class GenericCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: type[ModelType]):
        self.model = model
        logger.info(f"Initialized GenericCRUD for model: {model.__name__}")

    async def get(self, *, id: UUID | str, db_session: AsyncSession) -> ModelType | None:
        logger.debug(f"Fetching {self.model.__name__} with id: {id}")
        query = select(self.model).where(self.model.id == id)
        result = await db_session.execute(query)
        item = result.scalar_one_or_none()
        if item:
            logger.debug(f"Found {self.model.__name__} with id: {id}")
        else:
            logger.debug(f"No {self.model.__name__} found with id: {id}")
        return item

    async def get_by_ids(
        self, *, list_ids: list[UUID | str], db_session: AsyncSession
    ) -> Sequence[ModelType]:
        logger.debug(f"Fetching multiple {self.model.__name__}s with ids: {list_ids}")
        result = await db_session.execute(
            select(self.model).where(self.model.id.in_(list_ids))
        )
        items = result.scalars().unique().all()
        logger.debug(f"Found {len(items)} {self.model.__name__}s")
        return items

    async def get_count(self, db_session: AsyncSession | None = None) -> ModelType | None:
        logger.debug(f"Getting count of {self.model.__name__}")
        result = await db_session.execute(
            select(func.count()).select_from(select(self.model).subquery())
        )
        count = result.scalar()
        logger.debug(f"Total count of {self.model.__name__}: {count}")
        return count

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, query: Select[ModelType] | None = None, db_session: AsyncSession | None = None,
    ) -> list[ModelType]:
        logger.debug(f"Fetching multiple {self.model.__name__}s with skip: {skip}, limit: {limit}")
        if query is None:
            query = select(self.model).offset(skip).limit(limit).order_by(self.model.id)
        result = await db_session.execute(query)
        items = result.scalars().all()
        logger.debug(f"Retrieved {len(items)} {self.model.__name__}s")
        return items

    async def get_multi_paginated(
            self,
            *,
            params: Params = Params(),
            query: Select[ModelType] | None = None,
            db_session: AsyncSession
    ) -> Page[ModelType]:
        logger.debug(f"Fetching paginated {self.model.__name__}s with params: {params}")
        if query is None:
            query = select(self.model)
        result = await paginate(db_session, query, params)
        logger.debug(f"Retrieved page {result.page} of {self.model.__name__}s")
        return result

    async def create(
        self, *, obj_in: CreateSchemaType | ModelType | None = None, created_by_id: UUID | int | None = None, relationship_refresh: List, db_session: AsyncSession | None = None,
    ) -> ModelType:
        logger.info(f"Creating new {self.model.__name__}")
        try:
            if obj_in is None:
                if created_by_id is None:
                    logger.error("Neither obj_in nor created_by_id provided")
                    raise ValueError("Either obj_in or created_by_id must be provided")
                db_obj = self.model(id=created_by_id)
            elif not isinstance(obj_in, self.model):
                db_obj = self.model(**obj_in.model_dump())
            else:
                db_obj = obj_in

            if created_by_id:
                db_obj.id = created_by_id

            db_session.add(db_obj)
            await db_session.commit()
            await db_session.refresh(db_obj, relationship_refresh)
            logger.info(f"Successfully created {self.model.__name__} with id: {db_obj.id}")
            return db_obj
        except exc.IntegrityError as e:
            logger.error(f"Integrity error while creating {self.model.__name__}: {str(e)}")
            raise HTTPException(status_code=409, detail="Resource already exists")
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise

    async def update(
        self, *, obj_current: ModelType, obj_new: UpdateSchemaType | dict[str, Any] | ModelType, db_session: AsyncSession | None = None,
    ) -> ModelType:
        logger.info(f"Updating {self.model.__name__} with id: {obj_current.id}")
        try:
            if isinstance(obj_new, dict):
                update_data = obj_new
            else:
                update_data = obj_new.model_dump(exclude_unset=True)
            
            for field in update_data:
                logger.debug(f"Updating field {field}")
                setattr(obj_current, field, update_data[field])

            db_session.add(obj_current)
            await db_session.commit()
            await db_session.refresh(obj_current)
            logger.info(f"Successfully updated {self.model.__name__} with id: {obj_current.id}")
            return obj_current
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise

    async def remove(
        self, *, id: UUID | int, db_session: AsyncSession | None = None
    ) -> ModelType:
        logger.info(f"Removing {self.model.__name__} with id: {id}")
        try:
            result = await db_session.execute(select(self.model).where(self.model.id == id))
            obj = result.scalars().one_or_none()
            if not obj:
                logger.warning(f"No {self.model.__name__} found with id: {id}")
                return None
            await db_session.delete(obj)
            await db_session.commit()
            logger.info(f"Successfully removed {self.model.__name__} with id: {id}")
            return obj
        except Exception as e:
            logger.error(f"Error removing {self.model.__name__}: {str(e)}")
            raise

    def _get_table_names(self, connection):
        inspector = inspect(connection)
        return inspector.get_table_names()

    async def _check_association_table(self, model_instance: Type[Base], related_model: Type[Base], db_session: AsyncSession) -> tuple[str, str]:
        """
        Проверяет наличие промежуточной таблицы между моделями.
        Если таблицы нет, логирует ошибку и генерирует общее исключение для клиента.
        """
        model_name = model_instance.__class__.__name__.lower()
        related_model_name = related_model.__name__.lower()
        association_table_name = f"{model_name}_{related_model_name}_association"

        conn = await db_session.connection()
        table_names = await conn.run_sync(self._get_table_names)

        if association_table_name not in table_names:
            raise HTTPException(
                status_code=500,
                detail="Server Error: Association table is missing."
            )

        return model_name, association_table_name