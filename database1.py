from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from models import *

DATABASE_URL = settings.get_db_url()

# Создаем асинхронный движок для работы с базой данных
engine = create_async_engine(url=DATABASE_URL)
# Создаем фабрику сессий для взаимодействия с базой данных
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех моделей


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_user(username: str, email: str, password: str):
    async with async_session_maker() as session:
        async with session.begin():
            new_user = User(username=username, email=email, password=password)
            session.add(new_user)


async def is_email_registered(email: str):
    async with async_session_maker() as session:
        async with session.begin():
            query = select(User).filter_by(email=email)
            result = await session.execute(query)
            user = result.scalars().first()
            return user

async def get_user_by_id(id: int):
    async with async_session_maker() as session:
        async with session.begin():
            query = select(User).filter_by(id=id)
            result = await session.execute(query)
            user = result.scalars().first()
            return user

async def create_board(user_id: int):
    '''Получает на вход ид юзера и создает для него новую ПУСТУЮ доску,
    возвращает ID СОЗДАННОЙ ДОСКИ'''
    pass

async def get_board_by_user_id_and_board_id(user_id: int, board_id: int):
    '''Получает на вход ид юзера и ид доски
    возвращает класс доски из моделс
    *хз гарантируется или нет что доска и юзер существуют поэтому лучше как то обработать этот случай'''
    pass

async def create_text(user_id: int, board_id: int, text: str):
    '''Получает на вход ид юзера и ид доски
    создает текстовый объект на доске, те добавляет в джсон словарь по юзер ид и борд ид по ключу Texts
    ид_текстового_соо(само создается прост уникальное относ текст соо хз мб и не надо, решим потом) и сам текст'''
    pass