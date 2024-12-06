from config import settings
from models import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import logging
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, Profile, Board, user_board_association

logger = logging.getLogger(__name__)
DATABASE_URL = settings.get_db_url()

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_tables(engine):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        raise RuntimeError("An error occurred while creating tables.")


async def create_user(username: str, email: str, password: str, session: AsyncSession):
    try:
        new_user = User(username=username, email=email, password=password)
        session.add(new_user)
        await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error creating user {username}: {e}")
        raise RuntimeError("An error occurred while creating a user.")


async def is_email_registered(email: str, session: AsyncSession):
    try:
        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        user = result.scalars().first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error checking if email {email} is registered: {e}")
        raise RuntimeError("An error occurred while checking email registration.")


async def get_user_by_id(id: int, session: AsyncSession):
    try:
        query = select(User).filter_by(id=id)
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            raise ValueError(f"User with id {id} not found.")
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving user with id {id}: {e}")
        raise RuntimeError("An error occurred while retrieving the user.")


async def create_board(user_id: int, title: str, session: AsyncSession):
    try:
        query = select(User).filter_by(id=user_id)
        result = await session.execute(query)
        user = result.scalars().first()

        if not user:
            raise ValueError(f"User with id {user_id} not found")

        text_id = str(uuid.uuid4())
        new_board = Board(title=title, content={"texts": [{"id": text_id, "text": "goida"}]}, user_id=user.id)
        user.boards.append(new_board)
        session.add(new_board)
        await session.commit()
        return new_board.id
    except SQLAlchemyError as e:
        logger.error(f"Error creating board for user_id {user_id}: {e}")
        raise RuntimeError("An error occurred while creating a board.")


async def get_board_by_user_id_and_board_id(user_id: int, board_id: int, session: AsyncSession):
    """Возвращает данные доски по user_id и board_id"""
    try:
        query = (
            select(Board.content)
            .join(user_board_association, user_board_association.c.board_id == Board.id)
            .filter(user_board_association.c.user_id == user_id)
            .filter(user_board_association.c.board_id == board_id)
        )
        result = await session.execute(query)
        content = result.all()  # Получаем все результаты запроса
        if not content:
            raise ValueError(f"No board found for user_id {user_id} and board_id {board_id}.")
        return content[0][0]
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving board for user_id {user_id} and board_id {board_id}: {e}")
        raise RuntimeError("An error occurred while retrieving the board.")


async def create_text(board_id: int, text: str, session: AsyncSession):
    try:
        query = select(Board).filter(Board.id == board_id)
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
    except SQLAlchemyError as e:
        logger.error(f"Error adding text to board_id {board_id}: {e}")
        raise RuntimeError("An error occurred while adding text to the board.")


async def get_boards_by_user_id(user_id: int, session: AsyncSession):
    try:
        query = (
            select(Board.id, Board.title)
            .join(user_board_association, user_board_association.c.board_id == Board.id)
            .filter(user_board_association.c.user_id == user_id)
        )
        result = await session.execute(query)
        boards = result.all()  # Получаем все результаты запроса
        return [{"id": board.id, "title": board.title} for board in boards]

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching boards for user_id={user_id}: {e}")
        raise RuntimeError("Failed to fetch boards due to a database error.") from e


async def update_text(board_id: int, text_id: str, new_text: str, session: AsyncSession):
    try:
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
    
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating text with text_id={text_id} in board_id={board_id}: {e}")
        raise RuntimeError("Failed to update text due to a database error.") from e