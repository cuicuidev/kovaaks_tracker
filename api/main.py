from typing import Any, Annotated

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, Depends, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Entry(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    scenario: str = Field(index=True)
    score: float = Field(None)
    ctime: int = Field(None, index=True)
    sens_scale: str = Field(None)
    sens_increment: float = Field(None)
    dpi: int = Field(None)
    fov_scale: str = Field(None)
    fov: int = Field(None)

SQLITE_FILENAME = "database2.db"
SQLITE_URL = f"sqlite:///{SQLITE_FILENAME}"

CONNECT_ARGS = {"check_same_thread" : False}
engine = create_engine(SQLITE_URL, connect_args=CONNECT_ARGS)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/insert")
async def insert_entry(entry: Entry, session: SessionDep) -> Entry:
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@app.get("/select")
async def  select_entries(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100) -> list[Entry]:
    entries = session.exec(select(Entry).offset(offset).limit(limit)).all()
    return entries

@app.get("/latest")
async def latest(session: SessionDep) -> int:
    statement = select(Entry).order_by(Entry.ctime.desc())
    latest = session.exec(statement).first()
    if latest:
        return latest.ctime
    else:
        return 0