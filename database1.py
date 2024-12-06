from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
import uuid

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

async def create_board(user_id: int, title: str):
    async with async_session_maker() as session:
        async with session.begin():
            query = select(User).filter_by(id=user_id)
            result = await session.execute(query)
            user = result.scalars().first()

            if not user:
                raise ValueError(f"User with id {user_id} not found")
            text_id = str(uuid.uuid4())
            new_board = Board(title=title, content = {"texts": [{"id": text_id, "text": "goida"}]}, user_id=user.id)
            user.boards.append(new_board)
            session.add(new_board)
            await session.commit()
            return new_board.id

async def get_board_by_user_id_and_board_id(user_id: int, board_id: int):
    '''Возвращает данные доски по user_id и board_id'''
    async with async_session_maker() as session:
        async with session.begin():
            query = (
                select(Board.content)
                .join(user_board_association, user_board_association.c.board_id == Board.id)
                .filter(user_board_association.c.user_id == user_id)
                .filter(user_board_association.c.board_id == board_id)
            )
            result = await session.execute(query)
            content = result.all()  # Получаем все результаты запроса
            return content[0][0]


async def create_text(board_id: int, text: str):
    async with async_session_maker() as session:
        async with session.begin():
            query = (
                select(Board)
                .filter(Board.id == board_id)
            )
            result = await session.execute(query)
            board = result.scalars().first()

            if not board:
                raise ValueError(f"Board with id {board_id} not found")

            if board.content is None:
                board.content = {"texts": []}
            
            text_id = str(uuid.uuid4())
            new_content = dict(board.content)
            if "texts" not in new_content:
                new_content["texts"] = []
            existing_texts = new_content["texts"]
            new_content["texts"] = existing_texts + [{"id": text_id, "text": text}]
            board.content = new_content
            await session.commit()

    return text_id


async def get_boards_by_user_id(user_id : int):
    async with async_session_maker() as session:
        async with session.begin():
            query = (
                select(Board.id, Board.title)
                .join(user_board_association, user_board_association.c.board_id == Board.id)
                .filter(user_board_association.c.user_id == user_id)
            )
            result = await session.execute(query)
            boards = result.all()  # Получаем все результаты запроса
            return [{"id": board.id, "title": board.title} for board in boards]

async def update_text(board_id: int, text_id: str, new_text: str):
    async with async_session_maker() as session:
        async with session.begin():
            # Get the board
            query = select(Board).filter(Board.id == board_id)
            result = await session.execute(query)
            board = result.scalars().first()

            if not board:
                raise ValueError(f"Board with id {board_id} not found")

            # Make a completely new copy of the content
            new_content = {
                "texts": []
            }
            
            # Copy all texts, updating the one that matches
            text_found = False
            for text in board.content["texts"]:
                if text["id"] == text_id:
                    new_content["texts"].append({
                        "id": text_id,
                        "text": new_text
                    })
                    text_found = True
                else:
                    new_content["texts"].append(dict(text))

            if not text_found:
                raise ValueError(f"Text with id {text_id} not found")

            # Force SQLAlchemy to detect the change by reassigning the entire content
            board.content = new_content
            
            # Explicitly commit and make sure changes are saved
            await session.flush()
            await session.commit()
            
            # Verify the changes were saved
            await session.refresh(board)
            query2 = select(Board).filter(Board.id == board_id)
            result2 = await session.execute(query)
            board2 = result.scalars().first()
            # Double-check the content was updated
            for text in board2.content["texts"]:
                if text["id"] == text_id:
                    if text["text"] != new_text:
                        raise ValueError("Failed to save changes")
                    else:
                        print(text["text"])

    return True
