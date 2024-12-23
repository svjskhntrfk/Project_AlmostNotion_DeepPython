from contextlib import asynccontextmanager
from fastapi import Depends
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from starlette.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from router_notification import check_and_send_notifications
from datetime import datetime, timedelta

from database import *
from auth.transport.router_reg import router as reg_router
from router_boards import router as board_router
from router_profile import router as profile_router
from router_image import  router as image_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер, который управляет жизненным циклом приложения
    """
    await create_tables(engine)
    print("База готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)
app.include_router(reg_router)
app.include_router(board_router)
app.include_router(profile_router)
app.include_router(image_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Настраиваем планировщик для проверки дедлайнов TodoList
scheduler = AsyncIOScheduler()
scheduler.add_job(
    check_and_send_notifications,
    'interval',
    seconds=30,  # проверяем каждые 30 секунд
    kwargs={'session': async_session_maker()}
)
scheduler.start()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Get-запрос, отображает главную страницу

    Параметры:
        request (Request): Объект HTTP-запроса
    """
    return templates.TemplateResponse("landing.html", {"request": request})





