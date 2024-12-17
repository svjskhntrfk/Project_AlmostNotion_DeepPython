from config import settings
from models import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import logging
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, Profile, Board, user_board_association, Image, ImageCreate, ImageUpdate
from image_schemas import ImageDAOResponse
from sqlalchemy import UUID, Table, select, update
from fastapi import HTTPException, UploadFile
from typing import Type
from sqlalchemy.orm import aliased

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


async def create_user(username: str, email: str, password: str, session: AsyncSession):
    """
    Создает нового пользователя в базе данных.

    :param username: Имя пользователя.
    :param email: Электронная почта пользователя.
    :param password: Пароль пользователя.
    :param session: Асинхронная сессия SQLAlchemy.
    :raises RuntimeError: Если произошла ошибка при создании пользователя.
    """
    try:
        new_user = User(username=username, email=email, password=password)
        session.add(new_user)
        await session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Error creating user {username}: {e}")
        raise RuntimeError("An error occurred while creating a user.")



async def is_email_registered(email: str, session: AsyncSession):
    """
    Проверяет, зарегистрирован ли пользователь с указанной электронной почтой.

    :param email: Электронная почта пользователя.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если пользователь найден; иначе False.
    :raises RuntimeError: Если произошла ошибка при проверке электронной почты.
    """
    try:
        query = select(User).filter_by(email=email)
        result = await session.execute(query)
        user = result.scalars().first()
        return user
    except SQLAlchemyError as e:
        logger.error(f"Error checking if email {email} is registered: {e}")
        raise RuntimeError("An error occurred while checking email registration.")


async def get_user_by_id(id: int, session: AsyncSession):
    """
    Возвращает пользователя по его ID.

    :param id: ID пользователя.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Объект User, если пользователь найден.
    :raises ValueError: Если пользователь не найден.
    :raises RuntimeError: Если произошла ошибка при получении пользователя.
    """
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
    """
    Создает новую доску для пользователя.

    :param user_id: ID пользователя.
    :param title: Название доски.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: ID созданной доски.
    :raises ValueError: Если пользователь не найден.
    :raises RuntimeError: Если произошла ошибка при создании доски.
    """
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
    """
    Возвращает данные доски по ID пользователя и ID доски.

    :param user_id: ID пользователя.
    :param board_id: ID доски.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Содержимое доски в виде словаря.
    :raises ValueError: Если доска не найдена.
    :raises RuntimeError: Если произошла ошибка при получении данных доски.
    """
    try:
        query = (
            select(Board.title, Board.content)
            .join(user_board_association, user_board_association.c.board_id == Board.id)
            .filter(user_board_association.c.user_id == user_id)
            .filter(user_board_association.c.board_id == board_id)
        )
        result = await session.execute(query)
        result = result.all()[0]
        print(result)
        content = result.content  # Получаем все результаты запроса
        print(content)
        if not content:
            raise ValueError(f"No board found for user_id {user_id} and board_id {board_id}.")
        return result
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving board for user_id {user_id} and board_id {board_id}: {e}")
        raise RuntimeError("An error occurred while retrieving the board.")


async def create_text(board_id: int, text: str, session: AsyncSession):
    """
    Добавляет новый текст в доску.

    :param board_id: ID доски.
    :param text: Текст для добавления.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: ID добавленного текста.
    :raises ValueError: Если доска не найдена.
    :raises RuntimeError: Если произошла ошибка при добавлении текста.
    """
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

async def get_boards_by_user_id(user_id: int, session: AsyncSession) -> list[dict]:
    """
    Получает список досок, связанных с указанным пользователем.

    :param user_id: ID пользователя.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Список словарей, содержащих ID и названия досок.
             Пример: [{"id": 1, "title": "Board 1"}, {"id": 2, "title": "Board 2"}].
    :raises RuntimeError: Если произошла ошибка базы данных.
    """
    try:
        query = (
            select(Board.id, Board.title)
            .join(user_board_association, user_board_association.c.board_id == Board.id)
            .filter(user_board_association.c.user_id == user_id)
        )
        result = await session.execute(query)
        boards = result.all()
        return [{"id": board.id, "title": board.title} for board in boards]

    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching boards for user_id={user_id}: {e}")
        raise RuntimeError("Failed to fetch boards due to a database error.") from e


async def update_text(board_id: int, text_id: str, new_text: str, session: AsyncSession) -> bool:
    """
    Обновляет текст в указанной доске.

    :param board_id: ID доски, где нужно обновить текст.
    :param text_id: ID текста, который нужно обновить.
    :param new_text: Новый текст для замены.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если текст успешно обновлен.
    :raises ValueError: Если доска или текст не найдены.
    :raises RuntimeError: Если произошла ошибка базы данных при обновлении текста.
    """
    try:
        async with session.begin():
            # Получаем доску
            query = select(Board).filter(Board.id == board_id)
            result = await session.execute(query)
            board = result.scalars().first()

            if not board:
                raise ValueError(f"Board with id {board_id} not found")

            # Создаем новую копию контента
            new_content = {"texts": []}

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

            board.content = new_content
            await session.flush()  

            await session.refresh(board)
            for text in board.content["texts"]:
                if text["id"] == text_id and text["text"] != new_text:
                    raise ValueError("Failed to save changes")

        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error while updating text with text_id={text_id} in board_id={board_id}: {e}")
        raise RuntimeError("Failed to update text due to a database error.") from e


async def change_username(user_id: int, new_username: str, session: AsyncSession):
    """
    Изменяет имя пользователя в базе данных.

    :param user_id: ID пользователя.
    :param new_username: Новое имя пользователя.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если имя пользователя успешно изменено.
    :raises ValueError: Если изменения не удалось сохранить или пользователь не найден.
    :raises RuntimeError: Если произошла ошибка базы данных.
    """
    try:
        query = select(User).filter(User.id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()

        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        user.username = new_username
        await session.flush()  # Применяем изменения в текущей транзакции
        await session.commit()

        # Проверяем изменения
        await session.refresh(user)  # Обновляем объект из базы данных
        if user.username != new_username:
            raise ValueError("Failed to save changes")

        return True

    except SQLAlchemyError as e:
        logger.error(f"Error editing username for user_id={user_id}: {e}")
        raise RuntimeError("An error occurred while changing the username.") from e



async def change_password(user_id: int, new_password: str, session: AsyncSession):
    """
    Изменяет пароль пользователя в базе данных.

    :param user_id: ID пользователя.
    :param new_password: Новый пароль пользователя (хэшированный).
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если пароль успешно изменен.
    :raises ValueError: Если изменения не удалось сохранить или пользователь не найден.
    :raises RuntimeError: Если произошла ошибка базы данных.
    """
    try:
        query = select(User).filter(User.id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()

        if not user:
            raise ValueError(f"User with ID {user_id} not found.")

        user.password = new_password
        await session.flush()  
        await session.commit()  

        await session.refresh(user)
        if user.password != new_password:
            raise ValueError("Failed to save changes")

        return True

    except SQLAlchemyError as e:
        logger.error(f"Error editing password for user_id={user_id}: {e}")
        raise RuntimeError("An error occurred while changing the password.") from e

async def _reset_is_main(self, model_name: str, model_instance: Base, association_table_name: str,
                             db_session: AsyncSession):
    """Сбрасывает значение is_main для всех изображений, связанных с моделью."""
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
        stmt = (
            update(Image)
            .where(Image.id.in_(image_ids))
            .values(is_main=False)
        )
        await db_session.execute(stmt)
        await db_session.commit()

async def _get_image_url(self, db_obj: Image) -> ImageDAOResponse:
    """Получает URL к экземпляру Image."""
    url = await db_obj.storage.generate_url(db_obj.file)
    return ImageDAOResponse(image=db_obj, url=url)


async def create_with_file(
    self, *, file: UploadFile, is_main: bool, model_instance: Type[Base], path: str = "", db_session: AsyncSession | None = None
) -> Image | None:
    model_name, association_table_name = await self._check_association_table(
        model_instance=model_instance,
        related_model=self.model,
        db_session=db_session
    )

    if is_main:
        await self._reset_is_main(model_name, model_instance, association_table_name, db_session)

    db_obj = self.model(is_main=is_main)
    db_obj.file = await db_obj.storage.put_object(file, path)
    db_session.add(db_obj)
    await db_session.flush()

    association_table = Table(association_table_name, Base.metadata, autoload_with=db_session.bind)
    stmt = association_table.insert().values(**{f"{model_name}_id": model_instance.id, "image_id": db_obj.id})
    await db_session.execute(stmt)
    await db_session.commit()
    await db_session.refresh(db_obj)

    return db_obj

async def save_user_image(self, file: UploadFile, is_main: bool) -> Image:
    image = await create_with_file(
        file=file, is_main=is_main, model_instance=self.user, path=self.image_path, db_session=self.db_session
    )
    return image

