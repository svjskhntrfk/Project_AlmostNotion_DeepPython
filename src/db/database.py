from .cfg.config import settings
from .models import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import logging
from sqlalchemy import cast, Integer
from sqlalchemy.exc import SQLAlchemyError
from src.schemas import ImageCreate, ImageUpdate, ImageSchema
from sqlalchemy import UUID, Table, select, update, or_
from fastapi import HTTPException, UploadFile
from typing import Type
from sqlalchemy.orm import aliased
from src.backend.crud.image_crud import image_dao
from typing import List, Dict
from sqlalchemy.orm import selectinload
import traceback

logger = logging.getLogger(__name__)
DATABASE_URL = settings.get_db_url()

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Создает и предоставляет асинхронный сеанс SQLAlchemy для взаимодействия с базой данных.

    :return: Асинхронный генератор сессий SQLAlchemy.
    """
    async with async_session_maker() as session:
        yield session


async def create_tables(engine):
    """
    Создает все таблицы в базе данных, используя предоставленный SQLAlchemy движок.

    :param engine: SQLAlchemy AsyncEngine для подключения к базе данных.
    :raises RuntimeError: Если произошла ошибка при создании таблиц.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise RuntimeError("An error occurred while creating tables.")





