import os
import datetime
from typing import Annotated, Any

from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import status, HTTPException, Depends

from pydantic import BaseModel
from sqlmodel import select

from database import SessionDep, User

from dotenv import load_dotenv
load_dotenv()

ACCESS_TOKEN_EXP_DAYS = 7
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

class SignUpRequest(BaseModel):
    email: str
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

def verify_passwd(plain_passwd, hashed_passwd):
    return pwd_context.verify(plain_passwd, hashed_passwd)

def get_passwd_hash(passwd):
    return pwd_context.hash(passwd)

def get_user(session: SessionDep, username: str) -> User:
    user = session.exec(select(User).where(User.username == username)).first()
    if user:
        return user
    
def authenticate_user(session: SessionDep, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_passwd(password, user.hashed_passwd):
        return False
    return user

def create_access_token(data: dict, expires_delta: datetime.timedelta = datetime.timedelta(days=ACCESS_TOKEN_EXP_DAYS)):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.UTC) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate" : "Bearer"},
    )
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(session, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.is_active:
        return current_user
    raise HTTPException(status_code=400, detail="Inactive user")