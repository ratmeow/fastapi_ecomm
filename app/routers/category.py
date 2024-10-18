from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from app.backend.db_depends import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import CreateCategory
from sqlalchemy import insert, select, update
from app.models.category import Category
from slugify import slugify
from starlette import status
from app.routers.auth import get_current_user

router = APIRouter(prefix="/category",
                   tags=["category"])


@router.get("/all_categories")
async def get_all_categories(session: Annotated[AsyncSession, Depends(get_session)]):
    query = select(Category).where(Category.is_active)
    categories = await session.execute(query)
    return categories.scalars().all()


@router.post("/create")
async def create_category(session: Annotated[AsyncSession, Depends(get_session)],
                          category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin"):
        query = insert(Category).values(name=category.name,
                                        parent_id=category.parent_id,
                                        slug=slugify(category.name))
        await session.execute(query)
        await session.commit()

        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You must be admin user for this'
        )


@router.put("/update_category")
async def update_category(session: Annotated[AsyncSession, Depends(get_session)],
                          category_id: int,
                          new_category: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin"):
        query = select(Category).where(Category.id == category_id)
        request = await session.execute(query)
        category = request.scalar()
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There is no category found")

        query = update(Category).where(Category.id == category_id).values(name=new_category.name,
                                                                          slug=slugify(new_category.name),
                                                                          parent_id=new_category.parent_id)

        await session.execute(query)
        await session.commit()

        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category update is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You must be admin user for this'
        )


@router.delete("/delete")
async def delete_category(session: Annotated[AsyncSession, Depends(get_session)],
                          category_id: int,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin"):
        query = await session.execute(select(Category).where(Category.id == category_id))
        category = query.scalar()
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There is no category found")
        query = update(Category).where(Category.id == category_id).values(is_active=False)
        await session.execute(query)
        await session.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You must be admin user for this'
        )
