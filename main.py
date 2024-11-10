from contextlib import asynccontextmanager

from fastapi import FastAPI
from db import create_tables, delete_tables
from router import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await delete_tables()
    print("База очищена")
    await create_tables()
    print("База готова к работе")
    yield
    print("Выключение")

app = FastAPI(lifespan=lifespan)
app.include_router(users_router)