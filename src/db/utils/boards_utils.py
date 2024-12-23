from ..models import *
from ..database import *


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
