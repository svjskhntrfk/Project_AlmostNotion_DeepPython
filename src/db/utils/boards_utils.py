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
    

async def get_images_by_board_id(board_id: int, session: AsyncSession) -> List[Image]:
    logger.info(f"Starting get_images_by_board_id for board_id: {board_id}")
    try:
        # Проверяем существование доски
        board = await session.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
        
        # Получаем все изображения, связанные с доской через relationship
        images = board.images
        
        logger.info(f"Retrieved {len(images)} images for board_id: {board_id}")
        
        # Преобразуем изображения в схему
        return [ImageSchema.from_orm(image) for image in images]

    except HTTPException as e:
        logger.error(f"HTTPException in get_images_by_board_id: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error in get_images_by_board_id: {str(e)}", exc_info=True)
        raise RuntimeError("An unexpected error occurred while retrieving images.") from e
    

async def save_image_on_board(board_id: int, file: UploadFile, session: AsyncSession) -> Image:
    print(f"Starting save_image_on_board for board_id: {board_id}")
    try:
        # Получаем пользователя
        board = await session.get(Board, board_id)
        if not board:
            raise HTTPException(status_code=404, detail="User not found")

        print(f"Calling image_dao.create_with_file with path: Boards")
        image = await image_board_dao.create_with_file(
            file=file,
            board_instance=board,  # Передаем объект пользователя
            path="Boards",
            db_session=session
        )
        await session.commit()
        return image
    except Exception as e:
        print(f"Error in save_image_on_board: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

async def get_images_by_board_id(board_id: int, session: AsyncSession) -> List[ImageSchema]:
    """
    Возвращает список всех изображений, привязанных к указанной доске.
    
    :param board_id: Идентификатор доски
    :param session: Асинхронная сессия SQLAlchemy
    :return: Список объектов ImageSchema
    """
    print(f"Starting get_images_by_board_id for board_id: {board_id}")
    try:
        # Проверяем, существует ли доска
        board = await session.get(Board, board_id, options=[selectinload(Board.images)])
        if not board:
            raise HTTPException(status_code=404, detail="Board not found")
        
        images = board.images  # Используем загруженные изображения через relationship

        print(f"Retrieved {len(images)} images for board_id: {board_id}")
        logger.info(f"Retrieved {len(images)} images for board_id: {board_id}")

        return [ImageSchema.from_orm(image) for image in images]

    except HTTPException as e:
        print(f"HTTPException in get_images_by_board_id: {e.detail}")
        logger.error(f"HTTPException in get_images_by_board_id: {e.detail}")
        raise e
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError in get_images_by_board_id: {str(e)}")
        logger.error(f"SQLAlchemyError in get_images_by_board_id: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        logger.error(f"Traceback: {traceback_str}")
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        print(f"Error in get_images_by_board_id: {str(e)}")
        print(f"Error type: {type(e)}")
        logger.error(f"Error in get_images_by_board_id: {str(e)}")
        traceback_str = traceback.format_exc()
        print(f"Traceback: {traceback_str}")
        logger.error(f"Traceback: {traceback_str}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while retrieving images.")



async def create_todo_list(
    board_id: int, 
    title: str, 
    deadline: Optional[datetime], 
    session: AsyncSession
) -> int:
    """
    Создаёт новый список задач (ToDoList) в рамках указанной доски.
    """
    try:
        query = select(Board).filter(Board.id == board_id)
        result = await session.execute(query)
        board = result.scalars().first()

        if not board:
            raise ValueError(f"Board with id={board_id} not found.")

        new_list = ToDoList(
            title=title,
            deadline=deadline,
            board_id=board_id
        )
        session.add(new_list)
        await session.commit()
        await session.refresh(new_list)  # нужно, чтобы получить ID, если автогенерация

        return new_list.id

    except SQLAlchemyError as e:
        logger.error(f"Error creating ToDoList for board_id={board_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while creating ToDoList.")

async def get_todo_lists_by_board_id(
    board_id: int, 
    session: AsyncSession
) -> List[ToDoList]:
    """
    Возвращает список всех ToDoList, связанных с данной доской.
    """
    try:
        query = select(ToDoList).filter(ToDoList.board_id == board_id)
        result = await session.execute(query)
        todo_lists = result.scalars().all()
        return todo_lists
    except SQLAlchemyError as e:
        logger.error(f"Error fetching ToDoLists for board_id={board_id}: {e}")
        raise RuntimeError("An error occurred while fetching ToDoLists.")

async def update_todo_list(
    todo_list_id: int, 
    new_title: Optional[str], 
    new_deadline: Optional[datetime], 
    session: AsyncSession
) -> bool:
    """
    Изменяет заголовок и/или дедлайн для ToDoList.
    """
    try:
        query = select(ToDoList).filter(ToDoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"ToDoList with id={todo_list_id} not found.")

        if new_title is not None:
            todo_list.title = new_title
        if new_deadline is not None:
            todo_list.deadline = new_deadline

        await session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error updating ToDoList id={todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while updating ToDoList.")
    

async def delete_todo_list(
    todo_list_id: int, 
    session: AsyncSession
) -> bool:
    """
    Удаляет ToDoList и все связанные с ним задачи (cascade="all, delete-orphan").
    """
    try:
        query = select(ToDoList).filter(ToDoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"ToDoList with id={todo_list_id} not found.")

        await session.delete(todo_list)
        await session.commit()
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error deleting ToDoList id={todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while deleting ToDoList.")
    

async def create_task(
    todo_list_id: int,
    title: str,
    deadline: Optional[datetime],
    session: AsyncSession
) -> int:
    """
    Создаёт новую задачу (Task) в рамках указанного ToDoList.
    """
    try:
        query = select(ToDoList).filter(ToDoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"ToDoList with id={todo_list_id} not found.")

        new_task = Task(
            title=title,
            deadline=deadline,
            completed=False,
            todo_list=todo_list
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        return new_task.id

    except SQLAlchemyError as e:
        logger.error(f"Error creating Task for todo_list_id={todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while creating Task.")

async def get_todo_lists_by_board_id(
    board_id: int, 
    session: AsyncSession
) -> List[ToDoList]:
    """
    Возвращает список всех ToDoList, связанных с данной доской.
    """
    try:
        query = select(ToDoList).filter(ToDoList.board_id == board_id)
        result = await session.execute(query)
        todo_lists = result.scalars().all()
        return todo_lists
    except SQLAlchemyError as e:
        logger.error(f"Error fetching ToDoLists for board_id={board_id}: {e}")
        raise RuntimeError("An error occurred while fetching ToDoLists.")
    

async def update_todo_list(
    todo_list_id: int, 
    new_title: Optional[str], 
    new_deadline: Optional[datetime], 
    session: AsyncSession
) -> bool:
    """
    Изменяет заголовок и/или дедлайн для ToDoList.
    """
    try:
        query = select(ToDoList).filter(ToDoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"ToDoList with id={todo_list_id} not found.")

        if new_title is not None:
            todo_list.title = new_title
        if new_deadline is not None:
            todo_list.deadline = new_deadline

        await session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error updating ToDoList id={todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while updating ToDoList.")
    
async def delete_todo_list(
    todo_list_id: int, 
    session: AsyncSession
) -> bool:
    """
    Удаляет ToDoList и все связанные с ним задачи (cascade="all, delete-orphan").
    """
    try:
        query = select(ToDoList).filter(ToDoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"ToDoList with id={todo_list_id} not found.")

        await session.delete(todo_list)
        await session.commit()
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error deleting ToDoList id={todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while deleting ToDoList.")

async def create_task(
    todo_list_id: int,
    title: str,
    deadline: Optional[datetime],
    session: AsyncSession
) -> int:
    """
    Создаёт новую задачу (Task) в рамках указанного ToDoList.
    """
    try:
        query = select(ToDoList).filter(ToDoList.id == todo_list_id)
        result = await session.execute(query)
        todo_list = result.scalars().first()

        if not todo_list:
            raise ValueError(f"ToDoList with id={todo_list_id} not found.")

        new_task = Task(
            title=title,
            deadline=deadline,
            completed=False,
            todo_list=todo_list
        )
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)
        return new_task.id

    except SQLAlchemyError as e:
        logger.error(f"Error creating Task for todo_list_id={todo_list_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while creating Task.")
    
async def update_task(
    task_id: int,
    new_title: Optional[str],
    new_deadline: Optional[datetime],
    completed: Optional[bool],
    session: AsyncSession
) -> bool:
    """
    Обновляет поля задачи (title, deadline, completed).
    """
    try:
        query = select(Task).filter(Task.id == task_id)
        result = await session.execute(query)
        task = result.scalars().first()

        if not task:
            raise ValueError(f"Task with id={task_id} not found.")

        if new_title is not None:
            task.title = new_title
        if new_deadline is not None:
            task.deadline = new_deadline
        if completed is not None:
            task.completed = completed

        await session.commit()
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error updating Task id={task_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while updating Task.")

async def delete_task(
    task_id: int,
    session: AsyncSession
) -> bool:
    """
    Удаляет задачу.
    """
    try:
        query = select(Task).filter(Task.id == task_id)
        result = await session.execute(query)
        task = result.scalars().first()

        if not task:
            raise ValueError(f"Task with id={task_id} not found.")

        await session.delete(task)
        await session.commit()
        return True

    except SQLAlchemyError as e:
        logger.error(f"Error deleting Task id={task_id}: {e}")
        await session.rollback()
        raise RuntimeError("An error occurred while deleting Task.")


async def get_tasks_by_deadline(
    board_id: int,
    deadline_before: datetime,
    session: AsyncSession
) -> List[Task]:
    """
    Возвращает все задачи для доски (через связь с ToDoList) 
    с дедлайном <= deadline_before и у которых completed=False.
    """
    try:
        # Состыковываем таблицы Task и ToDoList, ToDoList.board_id == board_id
        query = (
            select(Task)
            .join(Task.todo_list)
            .where(ToDoList.board_id == board_id)
            .where(Task.deadline <= deadline_before)
            .where(Task.completed == False)
        )
        result = await session.execute(query)
        tasks = result.scalars().all()
        return tasks
    except SQLAlchemyError as e:
        logger.error(f"Error filtering tasks for board_id={board_id}: {e}")
        raise RuntimeError("An error occurred while filtering tasks.")

async def get_board_with_todo_lists(board_id: int, session: AsyncSession) -> Board:
    """
    Возвращает объект Board, загружая связанные ToDoList и Task.
    """
    from sqlalchemy.orm import selectinload

    query = (
        select(Board)
        .options(
            selectinload(Board.todo_lists).selectinload(ToDoList.tasks)
        )
        .filter(Board.id == board_id)
    )
    result = await session.execute(query)
    board = result.scalars().first()
    print("board", board)
    if not board:
        raise ValueError(f"Board with id={board_id} not found.")
    return board