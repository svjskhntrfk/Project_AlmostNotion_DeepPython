from pydantic import BaseModel

class UserInfoAdd(BaseModel):
    email: str
    name : str
    password : str

class UserId(UserInfoAdd):
    id : int