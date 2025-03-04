import os

from contextlib import asynccontextmanager


from fastapi import FastAPI


from database import create_db_and_tables

from auth import auth_router
from entry import entry_router
from user import user_router
from me import me_router
from download import download_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(entry_router)
app.include_router(user_router)
app.include_router(me_router)
app.include_router(download_router)

@app.get("/")
async def where():
    return os.getcwd()