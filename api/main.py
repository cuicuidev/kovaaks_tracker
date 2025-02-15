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
async def latest(session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]) -> int:
    statement = select(Entry).where(Entry.user_id == current_user.id).order_by(Entry.ctime.desc())
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

@app.get("/entries/voltaic-s5-intermediate")
async def get_voltaic_s5_intermediate(current_user: Annotated[User, Depends(get_current_active_user)], session: SessionDep) -> list[Entry]:
    # raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
    user_entries = select(Entry).where(Entry.user_id == current_user.id)
    voltaic_entries = user_entries.where(
        any([Entry.hash == hash for hash in VOLTAIC_S5_INTERMEDIATE])
    )
    return session.exec(voltaic_entries).all()

VOLTAIC_S5_INTERMEDIATE = [
    "830238e82c367ad2ba40df1da9968131", # PASU
    "86f9526f57828ad981f6c93b35811f94", # POPCORN
    "37975ba4bbbd5f9c593e7dbd72794baa", # 1W3TS
    "5c7668cf07b550bb2b7956f5709cf84e", # WW5T
    "ec8acdea37fa767767d705e389db1463", # FROGTAGON
    "47124ba125c1807fc7deb011c2f545a7", # FLOATING HEADS
    "b11e423dba738357ce774a01422e9d91", # PGT
    "ff38084d283c4e285150faee9c6b2832", # SNAKE TRACK
    "c4c11bf8a727b6e6c836138535bd0879", # AETHER
    "489b27e681807e0212eef50241bb0769", # GROUND
    "865d54422da5368dc290d1bbc2b9b566", # RAW CONTROL
    "a5fa9fbc3d55851b11534c60b85a9247", # CONTROLSPHERE
    "dfb397975f6fcec5bd2ebf3cd0b7a66a", # DOT TS
    "03d6156260b1b2b7893b746354b889c2", # EDDIE TS
    "ff777f42a21d6ddcf8791caf2821a2bd", # DRIFT TS
    "138c732d61151697949af4a3f51311fa", # FLY TS
    "e3b4fdab121562a8d4c8c2ac426c890c", # CONTROL TS
    "7cd5eee66632ebec0c33218d218ebf95", # PENTA BOUNCE
]

@app.get("/download/kovaaks_tracker.exe")
async def download_binary():
    filename = "kovaaks_tracker.exe"
    file_path = os.path.join("api/bin", filename)

    if os.path.exists(file_path):
        file_like = open(file_path, mode="rb")
        return StreamingResponse(file_like, media_type="application/octet-stream")
    else:
        raise HTTPException(status_code=404)

    
@app.get("/")
async def where():
    return os.getcwd()