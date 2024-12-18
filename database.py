from config import settings
from models import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import logging
from sqlalchemy import cast, Integer
from sqlalchemy.exc import SQLAlchemyError
from models import Base, User, Profile, Board, user_board_association

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
    :return: Объект User, если пользователь найден; иначе None.
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


async def get_user_by_id(id: int | str, session: AsyncSession):
    """
    Возвращает пользователя по его ID.

    :param id: ID пользователя (может быть строкой или целым числом)
    :param session: Асинхронная сессия SQLAlchemy
    :return: Объект User, если пользователь найден
    :raises ValueError: Если пользователь не найден
    :raises RuntimeError: Если произошла ошибка при получении пользователя
    """
    try:
        user_id = int(id)
        query = (
            select(User)
            .filter(User.id == cast(user_id, Integer))
        )
        result = await session.execute(query)
        user = result.scalars().first()
        if not user:
            raise ValueError(f"User with id {id} not found.")
        return user
    except ValueError as e:
        logger.error(f"Invalid user ID format: {id}")
        raise ValueError(f"Invalid user ID format: {id}")
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving user with id {id}: {e}")
        raise RuntimeError("An error occurred while retrieving the user.")


async def create_board(user_id: int, title: str, session: AsyncSession) -> int:
    """
    Создает новую доску для пользователя.

    :param user_id: ID пользователя, который создаёт доску.
    :param title: Название доски.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: ID созданной доски.
    :raises ValueError: Если пользователь не найден.
    :raises RuntimeError: Если произошла ошибка при создании доски.
    """
    try:
        logger.debug(f"Attempting to create board '{title}' for user_id {user_id}")
        
        # Получаем пользователя по ID
        query = select(User).filter_by(id=user_id)
        result = await session.execute(query)
        user = result.scalars().first()
        logger.debug(f"User found: {user}")

        if not user:
            logger.warning(f"User with id {user_id} not found")
            raise ValueError(f"User with id {user_id} not found")

        # Создаем новую доску с использованием owner_id
        text_id = str(uuid.uuid4())
        new_board = Board(
            title=title,
            content={"texts": [{"id": text_id, "text": "goida"}]},
            owner_id=user.id  # Используем owner_id вместо user_id
        )

        # Добавляем доску в список owned_boards пользователя
        user.owned_boards.append(new_board)
        session.add(new_board)

        await session.commit()
        logger.info(f"Board '{title}' created with id {new_board.id} for user_id {user_id}.")
        return new_board.id

    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemyError while creating board for user_id {user_id}: {e}")
        raise RuntimeError(f"An error occurred while creating a board: {e}") from e

    except ValueError as ve:
        logger.warning(f"ValueError: {ve}")
        raise ve

    except Exception as ex:
        logger.exception(f"Unexpected error while creating board for user_id {user_id}: {ex}")
        raise RuntimeError(f"An unexpected error occurred: {ex}") from ex


async def get_board_by_user_id_and_board_id(user_id: int, board_id: int, session: AsyncSession):
    """
    Возвращает данные доски по ID пользователя и ID доски.

    :param user_id: ID пользователя.
    :param board_id: ID доски.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Содержимое доски в виде объекта Board.
    :raises ValueError: Если доска не найдена или пользователь не имеет к ней доступа.
    :raises RuntimeError: Если произошла ошибка при получении данных доски.
    """
    try:
        # Проверяем, что пользователь связан с доской через many-to-many отношение
        query = (
            select(Board)
            .join(user_board_association, user_board_association.c.board_id == Board.id)
            .filter(user_board_association.c.user_id == user_id)
            .filter(Board.id == board_id)
        )
        result = await session.execute(query)
        board = result.scalars().first()
        
        if not board:
            raise ValueError(f"No board found for user_id {user_id} and board_id {board_id}.")

        return board  # Возвращаем объект Board
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving board for user_id {user_id} and board_id {board_id}: {e}")
        raise RuntimeError("An error occurred while retrieving the board.")


async def create_text(board_id: int, text: str, session: AsyncSession) -> str:
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
        # Получаем доску
        query = select(Board).filter(Board.id == board_id)
        result = await session.execute(query)
        board = result.scalars().first()

        if not board:
            raise ValueError(f"Board with id {board_id} not found")

        # Инициализируем content, если он равен None
        if board.content is None:
            board.content = {"texts": []}

        # Создаём новый текстовый элемент
        text_id = str(uuid.uuid4())
        new_text_entry = {"id": text_id, "text": text}

        # Добавляем новый текст в список текстов
        board.content.setdefault("texts", []).append(new_text_entry)

        session.add(board)  # Явно добавляем объект в сессию
        await session.commit()

        logger.info(f"Added new text with id {text_id} to board {board_id}.")
        return text_id

    except SQLAlchemyError as e:
        logger.error(f"Error adding text to board_id {board_id}: {e}")
        raise RuntimeError("An error occurred while adding text to the board.") from e


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
        # Получаем доски, которыми владеет пользователь
        owned_query = select(Board.id, Board.title).filter(Board.owner_id == user_id)
        # Получаем доски, связанные через many-to-many отношение
        associated_query = (
            select(Board.id, Board.title)
            .join(user_board_association, user_board_association.c.board_id == Board.id)
            .filter(user_board_association.c.user_id == user_id)
        )

        # Выполняем оба запроса
        owned_result = await session.execute(owned_query)
        associated_result = await session.execute(associated_query)

        # Объединяем результаты и убираем дубликаты
        boards = set(owned_result.all()) | set(associated_result.all())

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
        # Получаем доску
        query = select(Board).filter(Board.id == board_id)
        result = await session.execute(query)
        board = result.scalars().first()

        if not board:
            raise ValueError(f"Board with id {board_id} not found")

        # Инициализируем content, если он равен None
        if board.content is None:
            board.content = {"texts": []}

        # Создаем новую копию контента
        new_content = {"texts": []}

        text_found = False
        for text_item in board.content.get("texts", []):
            if text_item["id"] == text_id:
                new_content["texts"].append({
                    "id": text_id,
                    "text": new_text
                })
                text_found = True
            else:
                new_content["texts"].append(dict(text_item))

        if not text_found:
            raise ValueError(f"Text with id {text_id} not found")

        board.content = new_content
        session.add(board)  # Явно добавляем объект в сессию
        await session.commit()

        # Дополнительная проверка сохранения изменений
        await session.refresh(board)

        # Проверяем, что текст был обновлён
        for text_item in board.content.get("texts", []):
            if text_item["id"] == text_id and text_item["text"] != new_text:
                raise ValueError("Failed to save changes")

        logger.info(f"Text with id {text_id} in board {board_id} successfully updated.")
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


async def create_jwt_tokens(
    tokens: list[dict],
    user: User,
    device_id: str,
    session: AsyncSession
) -> None:
    """
    Создает несколько JWT токенов в базе данных.

    :param tokens: Список словарей с данными токенов, содержащими 'jti' и 'exp'.
    :param user: Объект пользователя.
    :param device_id: Идентификатор устройства.
    :param session: Асинхронная сессия SQLAlchemy.
    """
    try:
        logger.debug('Creating JWT tokens in database')
        issued_tokens = [
            IssuedJWTToken(
                subject=user,  # Обновлено для использования отношения subject
                jti=token['jti'],
                device_id=device_id,
                expired_time=token['exp']
            )
            for token in tokens
        ]
        logger.debug(f"Issued tokens: {issued_tokens}")
        session.add_all(issued_tokens)
        await session.commit()
        logger.debug('JWT tokens creation completed')
    except SQLAlchemyError as e:
        logger.error(f"Error creating JWT tokens for user_id={user.id}: {e}")
        raise RuntimeError("An error occurred while creating JWT tokens.") from e
