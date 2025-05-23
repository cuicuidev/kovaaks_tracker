import os
import datetime
from typing import Annotated

from fastapi import Depends
from sqlmodel import SQLModel, Field, create_engine, Session

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

CONNECT_ARGS = {}#{"check_same_thread" : False}
engine = create_engine(DATABASE_URL, connect_args=CONNECT_ARGS)

class User(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    username: str = Field(None, index=True)
    email: str = Field(None)
    hashed_passwd: str = Field(None)

    is_active: bool = Field(True)
    is_verified: bool = Field(True)
    created_at: datetime.datetime = Field(None)
    updated_at: datetime.datetime = Field(None)

class Entry(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    user_id: int | None = Field(None, foreign_key="user.id")
    scenario: str = Field(None)
    hash: str = Field(index=True)
    score: float = Field(None)
    ctime: str = Field(None, index=True)
    sens_scale: str = Field(None)
    sens_increment: float = Field(None)
    dpi: int = Field(None)
    fov_scale: str = Field(None)
    fov: int = Field(None)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]