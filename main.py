from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from starlette.requests import Request
from starlette.responses import HTMLResponse

from database import *
from router_reg import router as reg_router
from router_boards import router as board_router
from router_profile import router as profile_router
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("База готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)
app.include_router(reg_router)
app.include_router(board_router)
app.include_router(profile_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/registration", response_class=HTMLResponse)
async def registration_page(request: Request):
    return templates.TemplateResponse("reg.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("entry.html", {"request": request})

@app.get("/main_page/{user_id}", response_class=HTMLResponse)
async def main_page(user_id: str, request: Request):
    user = await get_user_by_id(int(user_id))
    boards_id_and_names = await get_boards_by_user_id(int(user_id))
    context = []
    for board in boards_id_and_names:
        context.append({"url":"/board/main_page/" + user_id + "/" + str(board["id"]), "name": board["title"]})

    return templates.TemplateResponse("main_page.html", {"request": request, "username": user.username, "user_id": user_id, "links" : context})




