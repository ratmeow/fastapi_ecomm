from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette import status
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_session
from app.schemas import CreateUser
from sqlalchemy import insert, select
from app.models.user import User
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.backend.config import settings

qauth2_schema = OAuth2PasswordBearer(tokenUrl="auth/token")

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_access_token(username: str, user_id: int, is_admin: bool, is_supplier: bool, is_customer: bool,
                              expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "is_admin": is_admin, "is_supplier": is_supplier,
              "is_customer": is_customer}
    expires = datetime.now() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, settings.JWT_KEY, settings.JWT_ALGORITHM)


async def authenticate(session: Annotated[AsyncSession, Depends(get_session)],
                       username: str, password: str):
    user = await session.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid authentication credentials",
                            headers={"WWW-Authenticate": "Bearer"},
                            )

    return user


async def get_current_user(token: Annotated[str, Depends(qauth2_schema)]):
    try:
        payload = jwt.decode(token, settings.JWT_KEY, algorithms=settings.JWT_ALGORITHM)
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: str = payload.get('is_admin')
        is_supplier: str = payload.get('is_supplier')
        is_customer: str = payload.get('is_customer')
        expire = payload.get('exp')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No access token supplied"
            )
        if datetime.now() > datetime.fromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token expired!"
            )

        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_supplier': is_supplier,
            'is_customer': is_customer,
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


@router.post("/")
async def create_user(session: Annotated[AsyncSession, Depends(get_session)], user: CreateUser):
    await session.execute(insert(User).values(
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        email=user.email,
        hashed_password=bcrypt_context.hash(user.password)
    ))
    await session.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.post("/token")
async def login(session: Annotated[AsyncSession, Depends(get_session)],
                form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user: User = await authenticate(session, form_data.username, form_data.password)

    if not user or user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    token = await create_access_token(user.username, user.id, user.is_admin, user.is_supplier, user.is_customer,
                                      expires_delta=timedelta(minutes=30))
    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.get("/read_current_user")
async def read_current_user(user: User = Depends(get_current_user)):
    return user
