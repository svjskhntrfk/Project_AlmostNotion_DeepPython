from ..models import *
from ..database import *

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