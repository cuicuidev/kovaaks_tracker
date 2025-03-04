from fastapi import status
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException

from sqlmodel import select


from database import User, SessionDep

user_router = APIRouter(prefix="/user", tags=["User"])

@user_router.get("/{username}")
async def get_user(username: str, session: SessionDep) -> User:
    user_query = select(User).where(User.username == username)
    maybe_user = session.exec(user_query).first()
    if maybe_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Username {username} does not exist")
    maybe_user.hashed_passwd = "REDACTED"
    return maybe_user

@user_router.get("/{username}")
async def initiate_verification_process(username: str):
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, detail=f"Email verification is not yet implemented. Sorry, {username}.")