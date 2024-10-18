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
from app.routers.auth import get_current_user
from sqlalchemy import select, update

router = APIRouter(
    prefix="/permission",
    tags=["permission"]
)


@router.patch("/")
async def supplier_permission(session: Annotated[AsyncSession, Depends(get_session)],
                              get_user: Annotated[dict, Depends(get_current_user)],
                              user_id: int):
    if get_user.get("is_admin"):
        user: User = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        if user.is_supplier:
            await session.execute(update(User).where(User.id == user_id).values(is_supplier=False, is_customer=True))
            await session.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is no longer supplier'
            }
        else:
            await session.execute(update(User).where(User.id == user_id).values(is_supplier=True, is_customer=False))
            await session.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is now supplier'
            }

    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have admin permission"
        )


@router.delete("/delete")
async def delete_user(session: Annotated[AsyncSession, Depends(get_session)],
                      get_user: Annotated[dict, Depends(get_current_user)],
                      user_id: int):
    if get_user.get("is_admin"):
        user: User = await session.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="You can't delete admin user"
            )

        if user.is_active:
            await session.execute(update(User).where(User.id == user_id).values(is_active=True))
            await session.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is deleted'
            }
        else:
            await session.execute(update(User).where(User.id == user_id).values(is_active=False))
            await session.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is activated'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You don't have admin permission"
        )
