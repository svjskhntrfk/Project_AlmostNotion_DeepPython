from ..models import *
from ..database import *

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

    :param user_id: ID ��ользователя.
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
