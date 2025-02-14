import os
import datetime
from typing import Annotated

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import select

from fastapi.security import OAuth2PasswordRequestForm

from database import create_db_and_tables, SessionDep, Entry, User
from auth import pwd_context, create_access_token, authenticate_user, SignUpRequest, Token, get_current_active_user

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/insert")
async def insert_entry(entry: Entry, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]) -> Entry:
    entry.user_id = current_user.id
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@app.get("/latest")
async def latest(session: SessionDep) -> int:
    statement = select(Entry).order_by(Entry.ctime.desc())
    latest = session.exec(statement).first()
    if latest:
        return latest.ctime
    else:
        return 0

@app.post("/auth/signup")
async def create_user(request: SignUpRequest, session: SessionDep) -> User:
    conflict = session.exec(select(User).where(
        User.username == request.username
        or User.email == request.email)).first()
    if conflict is not None:
        if conflict.email == request.email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Email {request.username} is already in use.")
        if conflict.username == request.username:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User {request.username} already exists.")
        
    hashed_password = pwd_context.hash(request.password)
    now = datetime.datetime.now(datetime.UTC)
    user = User(
        id=None,
        username=request.username,
        email=request.email,
        hashed_passwd=hashed_password,
        is_active=True,
        is_verified=False,
        created_at=now,
        updated_at=now
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.post("/auth/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user


@app.get("/users/me/entries")
async def read_own_entries(current_user: Annotated[User, Depends(get_current_active_user)], session: SessionDep) -> list[Entry]:
    entries = session.exec(select(Entry).where(Entry.user_id == current_user.id)).all()
    return entries

@app.get("/download/kovaaks_tracker.exe")
async def download_binary():
    filename = "kovaaks_tracker.exe"
    file_path = os.path.join("api/bin", filename)

    if os.path.exists(file_path):
        file_like = open(file_path, mode="rb")
        return StreamingResponse(file_like, media_type="application/octet-stream")
    else:
        return {"error" : "File not found"}
    
@app.get("/download/setup.exe")
async def download_setup():
    filename = "kovaaks_tracker_tool_setup.exe"
    file_path = os.path.join("api/bin", filename)
    print(file_path)

    if os.path.exists(file_path):
        file_like = open(file_path, mode="rb")
        return StreamingResponse(file_like, media_type="application/octet-stream")
    else:
        return {"error": "File not found"}