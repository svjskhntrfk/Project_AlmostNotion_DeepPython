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
    # Создаём пользователя
    username = "check_user"
    email = "check_user@example.com"
    password = "check_pass"
    await create_user(username, email, password, db_session)

    # Проверяем, что email зарегистрирован
    user = await is_email_registered(email, db_session)
    assert user is not None
    assert user.email == email

    # Проверяем несуществующий email
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
async def test_add_profile_data(db_session):
    # Создаём пользователя без профиля
    username = "profile_user"
    email = "profile_user@example.com"
    password = "prof_pass"
    await create_user(username, email, password, db_session)

    # Получаем ID вновь созданного пользователя
    result = await db_session.execute(select(User).filter_by(email=email))
    user = result.scalars().first()
    assert user is not None

    # Добавляем данные профиля
    await add_profile_data(user_id=user.id, session=db_session, first_name="John", last_name="Doe", age=30)

    # Проверяем, что данные профиля были добавлены
    result = await db_session.execute(select(User).filter_by(id=user.id))
    user_with_profile = result.scalars().first()
    assert user_with_profile.profile is not None
    assert user_with_profile.profile.first_name == "John"
    assert user_with_profile.profile.last_name == "Doe"
    assert user_with_profile.profile.age == 30

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