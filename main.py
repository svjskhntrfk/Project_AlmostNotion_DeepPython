from database1 import engine, async_session_maker, Base
from models import User
import asyncio


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_user(username: str, email: str, password: str):
    async with async_session_maker() as session:
        async with session.begin():
            new_user = User(username=username, email=email, password=password)
            session.add(new_user)

async def main():
    await create_tables()
    await create_user("sisipisi", 'popki.email.com', '12345')

if __name__ == "__main__":
    asyncio.run(main())