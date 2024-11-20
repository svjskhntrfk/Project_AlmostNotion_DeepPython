from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from database_1 import create_table, add_user, is_email_registered
from router_reg import router as reg_router
from starlette.requests import Request

from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    print("База готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)
app.include_router(reg_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})
  


