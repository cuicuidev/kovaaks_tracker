from typing import Annotated


from fastapi import Depends
from fastapi.routing import APIRouter

from sqlmodel import select



from database import SessionDep, Entry, User

from auth import get_current_active_user



me_router = APIRouter(prefix="/me", tags=["User"])

@me_router.get("/")
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]) -> User:
    return current_user

@me_router.post("/insert-entry")
async def insert_entry(entry: Entry, session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]) -> Entry:
    entry.user_id = current_user.id
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry

@me_router.get("/latest-entry-timestamp")
async def latest(session: SessionDep, current_user: Annotated[User, Depends(get_current_active_user)]) -> int:
    statement = select(Entry).where(Entry.user_id == current_user.id).order_by(Entry.ctime.desc())
    latest = session.exec(statement).first()
    if latest:
        return int(latest.ctime)
    else:
        return 0