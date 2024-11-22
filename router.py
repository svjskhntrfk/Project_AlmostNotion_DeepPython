from fastapi import APIRouter

from typing import Annotated
from fastapi.params import Depends

from schemas import UserInfoReg, UserId

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/tasks")
async def add_user(
        user : Annotated[UserInfoReg, Depends()],
):
    user_id = await UserRepo.add_one(user)
    return {"ok": True, "user_id": user_id}

@router.get("")
async def get_users() -> list[UserId]:
    users = await UserRepo.find_all()
    return users