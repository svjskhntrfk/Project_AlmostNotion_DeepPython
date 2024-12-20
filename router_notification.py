from typing import List
from fastapi import APIRouter, Form, Depends, Security
from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

class EmailSchema(BaseModel):
    email: List[EmailStr]


conf = ConnectionConfig(
    MAIL_USERNAME ="MindSpace",
    MAIL_PASSWORD = "Palma1234!",
    MAIL_FROM = "mindspace228@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


html = """
<p>Thanks for using Fastapi-mail</p> 
"""


@router.post("/email")
async def simple_send() -> JSONResponse:

    message = MessageSchema(
        subject="Fastapi-Mail module",
        recipients=["begimotik220@gmail.com"],
        body=html,
        subtype=MessageType.html)

    fm = FastMail(conf)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})     