import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User, Profile, Board
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from models import Base, User, Board
from database import *


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.mark.asyncio
async def test_create_tables(db_session):
    # Проверяем, что таблицы были созданы
    result = await db_session.execute(select(User))
    users = result.scalars().unique().all()
    assert isinstance(users, list)

@pytest.mark.asyncio
async def test_create_user(db_session):
    username = "test_user"
    email = "test_unique@example.com"
    password = "password123"

    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None
    assert user.username == username
    assert user.email == email
    assert user.password == password


@pytest.mark.asyncio
async def test_is_email_registered(db_session):
    username = "check_user"
    email = "check_user@example.com"
    password = "check_pass"
    await create_user(username, email, password, db_session)

    user = await is_email_registered(email, db_session)
    assert user is not None
    assert user.email == email

    no_user = await is_email_registered("no_exist@example.com", db_session)
    assert no_user is None

@pytest.mark.asyncio
async def test_get_user_by_id(db_session):
    # Создаём пользователя
    username = "id_test_user"
    email = "id_test_user@example.com"
    password = "pass_id"
    await create_user(username, email, password, db_session)

    # Получаем ID созданного пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()

    fetched_user = await get_user_by_id(user.id, db_session)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    assert fetched_user.email == user.email


@pytest.mark.asyncio
async def test_create_board(db_session):
    # Создаём пользователя
    username = "board_user"
    email = "board_user@example.com"
    password = "board_pass"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    title = "My Test Board"
    board_id = await create_board(user_id=user.id, title=title, session=db_session)

    # Проверяем, что доска создана
    result = await db_session.execute(select(Board).filter_by(id=board_id))
    board = result.scalars().first()
    assert board is not None
    assert board.title == title
    assert board.user_id == user.id

@pytest.mark.asyncio
async def test_get_board_by_user_id_and_board_id(db_session):
    # Создаём пользователя
    username = "board_user2"
    email = "board_user2@example.com"
    password = "board_pass2"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    title = "Second Board"
    board_id = await create_board(user_id=user.id, title=title, session=db_session)

    # Получаем контент доски
    content = await get_board_by_user_id_and_board_id(user_id=user.id, board_id=board_id, session=db_session)
    assert content is not None
    assert "texts" in content
    # По умолчанию в create_board добавляется текст "goida"
    assert len(content["texts"]) == 1
    assert content["texts"][0]["text"] == "goida"

@pytest.mark.asyncio
async def test_create_text(db_session):
    # Создаём пользователя
    username = "text_user"
    email = "text_user@example.com"
    password = "text_pass"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    # Создаём доску
    board_title = "Text Board"
    board_id = await create_board(user_id=user.id, title=board_title, session=db_session)

    # Добавляем новый текст
    new_text = "Hello World"
    text_id = await create_text(board_id, new_text, db_session)
    assert text_id is not None

    # Проверяем, что текст добавлен
    result = await db_session.execute(select(Board).filter_by(id=board_id))
    board = result.scalars().first()
    assert board is not None
    texts = board.content["texts"]
    # Был один "goida", теперь ещё один
    assert len(texts) == 2
    assert any(t["text"] == new_text for t in texts)

@pytest.mark.asyncio
async def test_get_boards_by_user_id(db_session):
    # Создаём пользователя
    username = "list_boards_user"
    email = "list_boards_user@example.com"
    password = "list_boards_pass"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    # Создаём несколько досок
    board_titles = ["BoardA", "BoardB", "BoardC"]
    for t in board_titles:
        await create_board(user_id=user.id, title=t, session=db_session)

    boards = await get_boards_by_user_id(user.id, db_session)
    assert len(boards) == 3
    returned_titles = [b["title"] for b in boards]
    assert set(returned_titles) == set(board_titles)

@pytest.mark.asyncio
async def test_change_username_success(db_session: AsyncSession):
    # Создаём пользователя
    username = "old_username"
    email = "test_user@example.com"
    password = "password123"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    # Меняем имя пользователя
    new_username = "new_username"
    success = await change_username(user_id=user.id, new_username=new_username, session=db_session)

    # Проверяем изменения
    assert success is True
    updated_user = await db_session.execute(select(User).filter_by(id=user.id))
    updated_user = updated_user.scalars().first()
    assert updated_user.username == new_username


@pytest.mark.asyncio
async def test_change_username_user_not_found(db_session: AsyncSession):
    # Попытка изменить имя пользователя для несуществующего ID
    invalid_user_id = 99999
    with pytest.raises(ValueError, match=f"User with ID {invalid_user_id} not found."):
        await change_username(user_id=invalid_user_id, new_username="nonexistent", session=db_session)


@pytest.mark.asyncio
async def test_change_password_success(db_session: AsyncSession):
    # Создаём пользователя
    username = "test_user"
    email = "password_user@example.com"
    password = "old_password"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    # Меняем пароль пользователя
    new_password = "new_password"
    success = await change_password(user_id=user.id, new_password=new_password, session=db_session)

    # Проверяем изменения
    assert success is True
    updated_user = await db_session.execute(select(User).filter_by(id=user.id))
    updated_user = updated_user.scalars().first()
    assert updated_user.password == new_password


@pytest.mark.asyncio
async def test_change_password_user_not_found(db_session: AsyncSession):
    # Попытка изменить пароль для несуществующего ID
    invalid_user_id = 99999
    with pytest.raises(ValueError, match=f"User with ID {invalid_user_id} not found."):
        await change_password(user_id=invalid_user_id, new_password="new_password", session=db_session)



@pytest.mark.asyncio
async def test_create_todo_list(db_session: AsyncSession):
    # Создаём пользователя
    username = "todo_user"
    email = "todo_user@example.com"
    password = "todo_pass"
    await create_user(username, email, password, db_session)

    # Получаем пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    # Создаём доску
    board_title = "Todo Board"
    board_id = await create_board(user_id=user.id, title=board_title, session=db_session)

    # Создаём список задач
    todo_title = "My Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)
    assert todo_list_id is not None

    # Проверяем, что список задач создан
    result = await db_session.execute(select(TodoList).filter_by(id=todo_list_id))
    todo_list = result.scalars().first()
    assert todo_list is not None
    assert todo_list.title == todo_title
    assert todo_list.board_id == board_id

@pytest.mark.asyncio
async def test_get_todo_lists(db_session: AsyncSession):
    # Создаём пользователя
    username = "get_todo_user"
    email = "get_todo_user@example.com"
    password = "get_todo_pass"
    user_id = await create_user(username, email, password, db_session)
    assert user_id is not None

    # Проверяем, что пользователь создан
    user = await db_session.execute(select(User).filter_by(id=user_id))
    user = user.scalars().first()
    assert user is not None

    # Создаём доску
    board_title = "Get Todo Board"
    board_id = await create_board(user_id=user.id, title=board_title, session=db_session)
    assert board_id is not None

    # Проверяем, что доска создана
    board = await db_session.execute(select(Board).filter_by(id=board_id))
    board = board.scalars().first()
    assert board is not None

    # Создаём несколько списков задач
    todo_titles = ["List 1", "List 2", "List 3"]
    for title in todo_titles:
        todo_list_id = await create_todo_list(board_id=board_id, title=title, session=db_session)
        assert todo_list_id is not None

    # Проверяем наличие созданных списков в базе
    created_todo_lists_result = await db_session.execute(select(TodoList).filter_by(board_id=board_id))
    created_todo_lists = created_todo_lists_result.scalars().unique().all()
    assert len(created_todo_lists) == len(todo_titles), "Number of created TodoLists does not match expected."

    # Получаем списки задач через функцию
    todo_lists = await get_todo_lists(board_id=board_id, session=db_session)
    assert len(todo_lists) == len(todo_titles)
    returned_titles = [tl["title"] for tl in todo_lists]
    assert set(returned_titles) == set(todo_titles)



@pytest.mark.asyncio
async def test_update_todo_list(db_session: AsyncSession):
    # Создаём пользователя, доску и список задач
    username = "update_todo_user"
    email = "update_todo_user@example.com"
    password = "update_todo_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Update Todo Board", session=db_session)

    todo_title = "Original Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    # Обновляем название списка задач
    new_title = "Updated Todo List"
    success = await update_todo_list(todo_list_id=todo_list_id, board_id=board_id, new_title=new_title, session=db_session)
    assert success is True

    # Проверяем изменения
    result = await db_session.execute(select(TodoList).filter_by(id=todo_list_id))
    todo_list = result.scalars().first()
    assert todo_list.title == new_title

@pytest.mark.asyncio
async def test_delete_todo_list(db_session: AsyncSession):
    # Создаём пользователя, доску и список задач
    username = "delete_todo_user"
    email = "delete_todo_user@example.com"
    password = "delete_todo_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Delete Todo Board", session=db_session)

    todo_title = "Delete Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    # Удаляем список задач
    success = await delete_todo_list(todo_list_id=todo_list_id, board_id=board_id, session=db_session)
    assert success is True

    # Проверяем, что список задач удален
    result = await db_session.execute(select(TodoList).filter_by(id=todo_list_id))
    todo_list = result.scalars().first()
    assert todo_list is None

@pytest.mark.asyncio
async def test_add_item_to_todo_list(db_session: AsyncSession):
    # Создаём пользователя, доску и список задач
    username = "add_item_user"
    email = "add_item_user@example.com"
    password = "add_item_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Add Item Board", session=db_session)

    todo_title = "Add Item Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    # Добавляем элемент задачи
    item_text = "Complete unit tests"
    item_id = await add_item_to_todo_list(todo_list_id=todo_list_id, text=item_text, session=db_session)
    assert item_id is not None

    # Проверяем, что элемент добавлен
    result = await db_session.execute(select(TodoItem).filter_by(id=item_id))
    todo_item = result.scalars().first()
    assert todo_item is not None
    assert todo_item.text == item_text
    assert not todo_item.completed

@pytest.mark.asyncio
async def test_update_todo_item(db_session: AsyncSession):
    # Создаём пользователя, доску, список задач и элемент задачи
    username = "update_item_user"
    email = "update_item_user@example.com"
    password = "update_item_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Update Item Board", session=db_session)

    todo_title = "Update Item Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    item_text = "Initial Task"
    item_id = await add_item_to_todo_list(todo_list_id=todo_list_id, text=item_text, session=db_session)
    assert item_id is not None

    # Обновляем элемент задачи
    new_text = "Updated Task"
    completed_status = True
    updated_item = await update_todo_item(
        todo_list_id=todo_list_id,
        item_id=item_id,
        new_text=new_text,
        completed=completed_status,
        session=db_session
    )
    assert updated_item.text == new_text
    assert updated_item.completed == completed_status

    # Проверяем изменения
    result = await db_session.execute(select(TodoItem).filter_by(id=item_id))
    todo_item = result.scalars().first()
    assert todo_item.text == new_text
    assert todo_item.completed == completed_status

@pytest.mark.asyncio
async def test_delete_todo_item(db_session: AsyncSession):
    # Создаём пользователя, доску, список задач и элемент задачи
    username = "delete_item_user"
    email = "delete_item_user@example.com"
    password = "delete_item_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Delete Item Board", session=db_session)

    todo_title = "Delete Item Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    item_text = "Task to be deleted"
    item_id = await add_item_to_todo_list(todo_list_id=todo_list_id, text=item_text, session=db_session)
    assert item_id is not None

    # Удаляем элемент задачи
    success = await delete_todo_item(todo_list_id=todo_list_id, item_id=item_id, session=db_session)
    assert success is True

    # Проверяем, что элемент задачи удален
    result = await db_session.execute(select(TodoItem).filter_by(id=item_id))
    todo_item = result.scalars().first()
    assert todo_item is None

@pytest.mark.asyncio
async def test_create_todo_list_board_not_found(db_session: AsyncSession):
    # Попытка создать список задач для несуществующей доски
    non_existent_board_id = 99999
    todo_title = "Non-existent Board Todo List"

    with pytest.raises(ValueError, match=f"Board with id {non_existent_board_id} not found."):
        await create_todo_list(board_id=non_existent_board_id, title=todo_title, session=db_session)

@pytest.mark.asyncio
async def test_add_item_to_todo_list_todo_list_not_found(db_session: AsyncSession):
    # Попытка добавить элемент задачи в несуществующий список задач
    non_existent_todo_list_id = 99999
    item_text = "Task for non-existent list"

    with pytest.raises(ValueError, match=f"Todo list with id {non_existent_todo_list_id} not found."):
        await add_item_to_todo_list(todo_list_id=non_existent_todo_list_id, text=item_text, session=db_session)

@pytest.mark.asyncio
async def test_update_todo_list_not_found(db_session: AsyncSession):
    # Попытка обновить несуществующий список задач
    non_existent_todo_list_id = 99999
    board_id = 1  # Предполагаемый ID доски, убедитесь, что он корректен или настройте соответствующим образом
    new_title = "Updated Title"

    with pytest.raises(ValueError, match=f"Todo list with id {non_existent_todo_list_id} not found in board {board_id}."):
        await update_todo_list(todo_list_id=non_existent_todo_list_id, board_id=board_id, new_title=new_title, session=db_session)

@pytest.mark.asyncio
async def test_update_todo_item_not_found(db_session: AsyncSession):
    # Попытка обновить несуществующий элемент задачи
    username = "update_item_fail_user"
    email = "update_item_fail_user@example.com"
    password = "update_item_fail_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Update Item Fail Board", session=db_session)

    todo_title = "Update Item Fail Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    non_existent_item_id = 99999
    new_text = "Non-existent Task"
    completed_status = False

    with pytest.raises(ValueError, match=f"Todo item with id {non_existent_item_id} not found."):
        await update_todo_item(
            todo_list_id=todo_list_id,
            item_id=non_existent_item_id,
            new_text=new_text,
            completed=completed_status,
            session=db_session
        )

@pytest.mark.asyncio
async def test_delete_todo_list_not_found(db_session: AsyncSession):
    # Попытка удалить несуществующий список задач
    non_existent_todo_list_id = 99999
    board_id = 1  # Предполагаемый ID доски, убедитесь, что он корректен или настройте соответствующим образом

    with pytest.raises(ValueError, match=f"Todo list with id {non_existent_todo_list_id} not found in board {board_id}."):
        await delete_todo_list(todo_list_id=non_existent_todo_list_id, board_id=board_id, session=db_session)

@pytest.mark.asyncio
async def test_delete_todo_item_not_found(db_session: AsyncSession):
    # Попытка удалить несуществующий элемент задачи
    username = "delete_item_fail_user"
    email = "delete_item_fail_user@example.com"
    password = "delete_item_fail_pass"
    await create_user(username, email, password, db_session)

    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    board_id = await create_board(user_id=user.id, title="Delete Item Fail Board", session=db_session)

    todo_title = "Delete Item Fail Todo List"
    todo_list_id = await create_todo_list(board_id=board_id, title=todo_title, session=db_session)

    non_existent_item_id = 99999

    with pytest.raises(ValueError, match=f"Todo item with id {non_existent_item_id} not found."):
        await delete_todo_item(todo_list_id=todo_list_id, item_id=non_existent_item_id, session=db_session)
