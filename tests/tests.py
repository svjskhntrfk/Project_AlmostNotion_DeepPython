import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.db import *
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


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
async def test_get_images_by_user_id(session: AsyncSession):
    # Создаем тестового пользователя
    user = User(username="testuser", email="test@example.com", password="hashedpassword")
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Добавляем изображения
    image1 = Image(file="path/to/image1.png", is_main=True, user_id=user.id)
    image2 = Image(file="path/to/image2.png", is_main=False, user_id=user.id)
    session.add_all([image1, image2])
    await session.commit()

    # Вызываем функцию
    images = await get_images_by_user_id(user.id, session)

    assert len(images) == 2
    assert images[0].file == "path/to/image1.png"
    assert images[1].file == "path/to/image2.png"
