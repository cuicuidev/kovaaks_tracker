import os
import datetime
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import status, HTTPException, Depends
from fastapi.routing import APIRouter

from pydantic import BaseModel
from sqlmodel import select

from database import SessionDep, User

from dotenv import load_dotenv
load_dotenv()

# ----------------------------------------- CONFIG -----------------------------------------

ACCESS_TOKEN_EXP_DAYS = 7
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ----------------------------------------- MODELS -----------------------------------------

class SignUpRequest(BaseModel):
    email: str
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# ----------------------------------------- HELPER FUNCTIONS -----------------------------------------

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

# ----------------------------------------- ENDPOINTS -----------------------------------------

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/signup")
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

@auth_router.post("/token")
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