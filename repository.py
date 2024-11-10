from sqlalchemy import select

from schemas import UserInfoAdd, UserId
from db import new_session, UserOrm


class UserRepo:
    @classmethod
    async def add_one(cls, data : UserInfoAdd):
        async with new_session() as session:
            user_dict = data.model_dump()

            user = UserOrm(**user_dict)
            session.add(user)
            await session.flush()
            await session.commit()
            return user.id

    @classmethod
    async def find_all(cls) -> list[UserId]:
        async with new_session() as session:
            query = select(UserOrm)
            result = await session.execute(query)
            user_models = result.scalars().all()
            user_schemas = [UserId.model_validate(user_model) for user_model in user_models]
            return user_schemas