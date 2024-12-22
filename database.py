from config import settings
from models import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
import uuid
import logging
from sqlalchemy import cast, Integer
from sqlalchemy.exc import SQLAlchemyError
from image_schemas import ImageCreate, ImageUpdate
from sqlalchemy import UUID, Table, select, update, or_
from fastapi import HTTPException, UploadFile
from typing import Type
from sqlalchemy.orm import aliased
from backend.src.crud.image_crud import image_dao
from models import *
from typing import List, Dict
from sqlalchemy.orm import selectinload
from image_schemas import ImageSchema
import traceback


logger = logging.getLogger(__name__)
DATABASE_URL = f"postgresql+asyncpg://postgres:postgres@postgres:5432/mydatabase"

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
    email = email.lower()
    user = User(username=username, email=email, password=password)
    session.add(user)
    try:
        await session.commit()
        await session.refresh(user)
        logger.info(f"User created with id: {user.id}")
        return user.id
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Error creating user: {e}")
        raise RuntimeError(f"Error creating user: {e}")



async def is_email_registered(email: str, session: AsyncSession):
    """
    Проверяет, зарегистрирован ли пользователь с указанной электронной почтой.

    :param email: Электронная почта пользователя.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если пользователь найден; иначе False.
    :raises RuntimeError: Если произошла ошибка при проверке электронной почты.
    """
    try:
        email = email.lower()
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
    В��звращает данные доски по ID пользователя и ID доски.

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
            .join(board_collaborators, board_collaborators.c.board_id == Board.id)
            .filter(board_collaborators.c.user_id == user_id)
            .filter(board_collaborators.c.board_id == board_id)
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
            .join(board_collaborators, board_collaborators.c.board_id == Board.id)
            .filter(board_collaborators.c.user_id == user_id)
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
        await session.commit()  

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

    
async def create_jwt_tokens(
  tokens: list[dict], 
  user: User, 
  device_id: str, 
  session: AsyncSession
) -> None:
  print('in database')
  """
  Create multiple JWT tokens in database

  Args:
      tokens: List of token payloads containing 'jti' and 'exp'
      user: User instance
      device_id: Device identifier
      session: AsyncSession instance
  """

  try:
    issued_tokens = [
        IssuedJWTToken(
            subject=user,
            jti=token['jti'],
            device_id=device_id,
            expired_time=token['exp']
      )
      for token in tokens
  ]
    print(issued_tokens)
    print('end')
    session.add_all(issued_tokens)
    await session.commit()

  except SQLAlchemyError as e:
        logger.error(f"Database error while creating JWT tokens for user_id {user.id}: {str(e)}")
        await session.rollback()
        raise RuntimeError("Failed to create JWT tokens") from e



async def save_user_image(user_id: int, file: UploadFile, is_main: bool, session: AsyncSession) -> Image:
    print(f"Starting save_user_image for user_id: {user_id}")
    try:
        # Получаем пользователя
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        print(f"Calling image_dao.create_with_file with path: Users")
        image = await image_dao.create_with_file(
            file=file,
            is_main=is_main,
            model_instance=user,  # Передаем объект пользователя
            path="Users",
            db_session=session
        )
        await session.commit()
        return image
    except Exception as e:
        print(f"Error in save_user_image: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

async def get_images_by_user_id(user_id: int, session: AsyncSession) -> List[Image]:
    print(f"Starting get_images_by_user_id for user_id: {user_id}")
    try:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        query = (
            select(Image)
            .outerjoin(user_image_association, Image.id == user_image_association.c.image_id)
            .where(or_(Image.user_id == user_id, user_image_association.c.user_id == user_id))
            .options(selectinload(Image.user))  # Опционально: загрузка связанных пользователей
        )

        result = await session.execute(query)
        images = result.scalars().all()

        print(f"Retrieved {len(images)} images for user_id: {user_id}")
        logger.info(f"Retrieved {len(images)} images for user_id: {user_id}")

        return [ImageSchema.from_orm(image) for image in images]

    except HTTPException as e:
        print(f"HTTPException in get_images_by_user_id: {e.detail}")
        logger.error(f"HTTPException in get_images_by_user_id: {e.detail}")
        raise e
    except Exception as e:
        print(f"Error in get_images_by_user_id: {str(e)}")
        print(f"Error type: {type(e)}")
        logger.error(f"Error in get_images_by_user_id: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        logger.error(f"Traceback: {traceback_str}")
        raise RuntimeError("An unexpected error occurred while retrieving images.") from e

async def get_image_url(image_id: str, session: AsyncSession) -> str:
    image = await image_dao.get(id=image_id, db_session=session)
    return image.url


async def delete_image(image_id: UUID, session: AsyncSession) -> None:
    """
    Удаляет изображение по его ID, удаляет файл из хранилища и удаляет все связи с пользователями.

    Args:
        image_id (UUID): ID изображения, которое нужно удалить.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Raises:
        HTTPException: Если изображение не найдено.
        RuntimeError: Если произошла ошибка при удалении изображения.
    """
    print(f"Starting delete_image for image_id: {image_id}")
    logger.info(f"Starting delete_image for image_id: {image_id}")
    try:
        image = await session.get(Image, image_id)
        if not image:
            logger.error(f"Image with id {image_id} not found.")
            raise HTTPException(status_code=404, detail="Image not found")

        if image.file:
            try:
                print(f"Deleting file from storage: {image.file}")
                logger.info(f"Deleting file from storage: {image.file}")
                await image.storage.delete_object(image.file)
            except Exception as file_error:
                logger.error(f"Failed to delete file {image.file} from storage: {file_error}")
                raise RuntimeError(f"Failed to delete file from storage: {file_error}") from file_error

        try:
            stmt = user_image_association.delete().where(user_image_association.c.image_id == image_id)
            await session.execute(stmt)
            logger.info(f"Deleted associations for image_id: {image_id}")
        except Exception as assoc_error:
            logger.error(f"Failed to delete associations for image_id {image_id}: {assoc_error}")
            raise RuntimeError(f"Failed to delete associations: {assoc_error}") from assoc_error

        try:
            await session.delete(image)
            await session.commit()
            logger.info(f"Successfully deleted image with ID: {image_id}")
            print(f"Successfully deleted image with ID: {image_id}")
        except Exception as db_error:
            await session.rollback()
            logger.error(f"Failed to delete image with id {image_id}: {db_error}")
            print(f"Failed to delete image with id {image_id}: {db_error}")
            raise RuntimeError(f"Failed to delete image: {db_error}") from db_error

    except HTTPException as e:
        logger.error(f"HTTPException in delete_image: {e.detail}")
        print(f"HTTPException in delete_image: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in delete_image: {str(e)}")
        print(f"Error in delete_image: {str(e)}")
        traceback_str = traceback.format_exc()
        logger.error(f"Traceback: {traceback_str}")
        print(f"Traceback: {traceback_str}")
        raise RuntimeError("An unexpected error occurred while deleting the image.") from e

async def add_collaborator(user_id: int, board_id: int, session: AsyncSession):
    try:
        # Get the board
        board_query = select(Board).filter(Board.id == board_id)
        board_result = await session.execute(board_query)
        board = board_result.scalars().first()
        
        if not board:
            raise ValueError(f"Board with ID {board_id} not found")

        user = await get_user_by_id(user_id, session)
        print('in add_collaborator', user   )
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Add the user to collaborators
        board.collaborators.append(user)
        await session.commit()
        
    except SQLAlchemyError as e:
        logger.error(f"Error adding collaborator to board_id={board_id}: {e}")
        raise RuntimeError("An error occurred while adding a collaborator to the board.") from e