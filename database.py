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
from sqlalchemy import UUID, Table, select, update
from fastapi import HTTPException, UploadFile
from typing import Type
from sqlalchemy.orm import aliased
from backend.src.crud.image_crud import image_dao
from models import *
from typing import List, Dict
from sqlalchemy.orm import selectinload


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
        return result[1]
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
    :raises RuntimeError: Если произошл�� ошибка базы данных при обновлении текста.
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

    

async def create_todo_list(board_id: int, title: str, session: AsyncSession) -> int:
    """
    Создает новый "to-do" список для указанной доски.

    :param board_id: ID доски.
    :param title: Заголовок "to-do" списка.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: ID созданного "to-do" списка.
    :raises ValueError: Если доска не найдена.
    :raises RuntimeError: Если произошла ошибка при создании "to-do" списка.
    """
    try:
        # Проверка существования доски
        query = select(Board).filter(Board.id == board_id)
        result = await session.execute(query)
        board = result.scalars().first()
        if not board:
            raise ValueError(f"Board with id {board_id} not found.")
        
        # Создание "to-do" списка
        new_todo_list = TodoList(title=title, board_id=board_id)
        session.add(new_todo_list)
        await session.commit()
        await session.refresh(new_todo_list)
        logger.info(f"Created new todo list with id {new_todo_list.id} on board {board_id}.")
        return new_todo_list.id
    except SQLAlchemyError as e:
        logger.error(f"Error creating todo list on board_id {board_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while creating a todo list.")
    
async def get_todo_lists(board_id: int, session: AsyncSession) -> List[Dict]:
    """
    Получает все "to-do" списки на указанной доске.

    :param board_id: ID доски.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Список "to-do" списков.
    :raises ValueError: Если доска не найдена.
    :raises RuntimeError: Если произошла ошибка при получении данных.
    """
    try:
        query = (
            select(TodoList)
            .filter(TodoList.board_id == board_id)
            .options(selectinload(TodoList.items))
        )
        result = await session.execute(query)
        todo_lists = result.scalars().unique().all()
        return [
            {
                "id": tl.id,
                "title": tl.title,
                "items": [
                    {"id": item.id, "text": item.text, "completed": item.completed}
                    for item in tl.items
                ],
            }
            for tl in todo_lists
        ]
    except SQLAlchemyError as e:
        logger.error(f"Error retrieving todo lists: {e}")
        raise RuntimeError("An error occurred while retrieving todo lists.")
    
async def update_todo_list(board_id: int, todo_list_id: int, new_title: str, session: AsyncSession) -> bool:
    """
    Обновляет заголовок "to-do" списка на указанной доске.

    :param board_id: ID доски.
    :param todo_list_id: ID "to-do" списка.
    :param new_title: Новый заголовок.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если обновление успешно.
    :raises ValueError: Если доска или "to-do" список не найдены.
    :raises RuntimeError: Если произошла ошибка при обновлении.
    """
    try:
        query = select(TodoList).filter(TodoList.id == todo_list_id, TodoList.board_id == board_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"Todo list with id {todo_list_id} not found in board {board_id}.")

        todo_list.title = new_title
        await session.commit()
        logger.info(f"Updated todo list {todo_list_id}.")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error updating todo list {todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while updating the todo list.")

async def delete_todo_list(board_id: int, todo_list_id: int, session: AsyncSession) -> bool:
    """
    Удаляет "to-do" список с указанной доски.

    :param board_id: ID доски.
    :param todo_list_id: ID "to-do" списка.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если удаление успешно.
    :raises ValueError: Если доска или "to-do" список не найдены.
    :raises RuntimeError: Если произошла ошибка при удалении.
    """
    try:
        query = select(TodoList).filter(TodoList.id == todo_list_id, TodoList.board_id == board_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"Todo list with id {todo_list_id} not found in board {board_id}.")

        await session.delete(todo_list)
        await session.commit()
        logger.info(f"Deleted todo list {todo_list_id}.")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error deleting todo list {todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while deleting the todo list.")

async def add_item_to_todo_list(todo_list_id: int, text: str, session: AsyncSession) -> int:
    """
    Добавляет новый элемент в указанный "to-do" список.

    :param todo_list_id: ID "to-do" списка.
    :param text: Текст задачи.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: ID добавленного элемента.
    :raises ValueError: Если "to-do" список не найден.
    :raises RuntimeError: Если произошла ошибка при добавлении элемента.
    """
    try:
        query = select(TodoList).filter(TodoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"Todo list with id {todo_list_id} not found.")

        new_item = TodoItem(text=text, todo_list_id=todo_list_id)
        session.add(new_item)
        await session.commit()
        await session.refresh(new_item)
        logger.info(f"Added item {new_item.id} to todo list {todo_list_id}.")
        return new_item.id

    except SQLAlchemyError as e:
        logger.error(f"Error adding item to todo list {todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while adding an item to the todo list.")

async def update_todo_item(todo_list_id: int, item_id: int, new_text: str, completed: bool, session: AsyncSession) -> bool:
    """
    Обновляет элемент в указанном "to-do" списке.

    :param todo_list_id: ID "to-do" списка.
    :param item_id: ID элемента.
    :param new_text: Новый текст задачи.
    :param completed: Статус выполнения задачи.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если обновление успешно.
    :raises ValueError: Если "to-do" список или элемент не найдены.
    :raises RuntimeError: Если произошла ошибка при обновлении элемента.
    """
    try:
        query = select(TodoItem).filter(TodoItem.id == item_id, TodoItem.todo_list_id == todo_list_id)
        result = await session.execute(query)
        todo_item = result.scalars().first()

        if not todo_item:
            raise ValueError(f"Todo item with id {item_id} not found in todo list {todo_list_id}.")

        todo_item.text = new_text
        todo_item.completed = completed
        await session.commit()
        logger.info(f"Updated todo item {item_id} in todo list {todo_list_id}.")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error updating todo item {item_id} in todo list {todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while updating the todo item.")

async def delete_todo_item(todo_list_id: int, item_id: int, session: AsyncSession) -> bool:
    """
    Удаляет элемент из указанного "to-do" списка.

    :param todo_list_id: ID "to-do" списка.
    :param item_id: ID элемента.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: True, если удаление успешно.
    :raises ValueError: Если "to-do" список или элемент не найдены.
    :raises RuntimeError: Если произошла ошибка при удалении элемента.
    """
    try:
        query = select(TodoItem).filter(TodoItem.id == item_id, TodoItem.todo_list_id == todo_list_id)
        result = await session.execute(query)
        todo_item = result.scalars().first()

        if not todo_item:
            raise ValueError(f"Todo item with id {item_id} not found in todo list {todo_list_id}.")

        await session.delete(todo_item)
        await session.commit()
        logger.info(f"Deleted todo item {item_id} from todo list {todo_list_id}.")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error deleting todo item {item_id} from todo list {todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while deleting the todo item.")

async def update_todo_item(todo_list_id: int, item_id: int, new_text: Optional[str], completed: Optional[bool], session: AsyncSession) -> TodoItem:
    """
    Обновляет элемент в указанном "to-do" списке.

    :param todo_list_id: ID "to-do" списка.
    :param item_id: ID элемента.
    :param new_text: Новый текст задачи.
    :param completed: Статус выполнения задачи.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Обновленный объект TodoItem.
    :raises ValueError: Если "to-do" список или элемент не найдены.
    :raises RuntimeError: Если произошла ошибка при обновлении элемента.
    """
    try:
        query = select(TodoItem).filter(TodoItem.id == item_id, TodoItem.todo_list_id == todo_list_id)
        result = await session.execute(query)
        todo_item = result.scalars().first()

        if not todo_item:
            raise ValueError(f"Todo item with id {item_id} not found in todo list {todo_list_id}.")

        if new_text is not None:
            todo_item.text = new_text
        if completed is not None:
            todo_item.completed = completed

        await session.commit()
        await session.refresh(todo_item)
        logger.info(f"Updated todo item {item_id} in todo list {todo_list_id}.")
        return todo_item

    except SQLAlchemyError as e:
        logger.error(f"Error updating todo item {item_id} in todo list {todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while updating the todo item.")

async def get_todo_list_by_id(todo_list_id: int, session: AsyncSession) -> Dict:
    """
    Получает "to-do" список по его ID.

    :param todo_list_id: ID "to-do" списка.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Словарь с данными "to-do" списка.
    :raises ValueError: Если "to-do" список не найден.
    :raises RuntimeError: Если произошла ошибка при получении данных.
    """
    try:
        query = select(TodoList).filter(TodoList.id == todo_list_id).options(selectinload(TodoList.items))
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"Todo list with id {todo_list_id} not found.")

        return {
            "id": todo_list.id,
            "title": todo_list.title,
            "items": [{
                "id": item.id,
                "text": item.text,
                "completed": item.completed
            } for item in todo_list.items]
        }

    except SQLAlchemyError as e:
        logger.error(f"Error retrieving todo list {todo_list_id}: {e}")
        raise RuntimeError("An error occurred while retrieving the todo list.")

async def get_todo_item_by_id(item_id: int, session: AsyncSession) -> Dict:
    """
    Получает элемент "to-do" списка по его ID.

    :param item_id: ID элемента.
    :param session: Асинхронная сессия SQLAlchemy.
    :return: Словарь с данными элемента.
    :raises ValueError: Если элемент не найден.
    :raises RuntimeError: Если произошла ошибка при получении данных.
    """
    try:
        query = select(TodoItem).filter(TodoItem.id == item_id)
        result = await session.execute(query)
        todo_item = result.scalars().first()

        if not todo_item:
            raise ValueError(f"Todo item with id {item_id} not found.")

        return {
            "id": todo_item.id,
            "text": todo_item.text,
            "completed": todo_item.completed
        }

    except SQLAlchemyError as e:
        logger.error(f"Error retrieving todo item {item_id}: {e}")
        raise RuntimeError("An error occurred while retrieving the todo item.")






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


async def save_user_image(user_id : int, file: UploadFile, is_main: bool, session: AsyncSession) -> Image:
    user =  await get_user_by_id(user_id, session)
    image_path = "Users"
    image = await image_dao.create_with_file(
        file=file, is_main=is_main, model_instance=user, path=image_path, db_session=session
    )
    return image

