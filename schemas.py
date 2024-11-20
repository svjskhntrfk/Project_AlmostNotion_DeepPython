from pydantic import BaseModel, EmailStr, Field, validator
class UserInfoReg(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта")
    name : str = Field(..., min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    password : str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")
    password_again : str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")

class UserInfoAuth(BaseModel):
    email: EmailStr = Field(..., description="Электронная почта")
    name : str = Field(..., min_length=3, max_length=50, description="Имя, от 3 до 50 символов")
    password : str = Field(..., min_length=5, max_length=50, description="Пароль, от 5 до 50 знаков")

class UserId(UserInfoReg):
    id : int