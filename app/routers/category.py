from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from app.backend.db_depends import get_session
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.schemas import CreateCategory
from sqlalchemy import insert, select, update
from app.models.category import Category
from slugify import slugify
from starlette import status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/category",
                   tags=["category"])


@router.get("/all_categories")
async def get_all_categories(session: Annotated[Session, Depends(get_session)]):
    query = select(Category).where(Category.is_active)
    categories = session.execute(query).scalars().all()
    return categories


@router.post("/create")
async def create_category(session: Annotated[Session, Depends(get_session)],
                          category: CreateCategory):
    query = insert(Category).values(name=category.name,
                                    parent_id=category.parent_id,
                                    slug=slugify(category.name))
    session.execute(query)
    session.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.put("/update_category")
async def update_category(session: Annotated[Session, Depends(get_session)],
                          category_id: int,
                          new_category: CreateCategory):
    query = select(Category).where(Category.id == category_id)
    category = session.execute(query).scalar()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There is no category found")

    query = update(Category).where(Category.id == category_id).values(name=new_category.name,
                                                                      slug=slugify(new_category.name),
                                                                      parent_id=new_category.parent_id)

    session.execute(query)
    session.commit()

    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Category update is successful'
    }

    
@router.delete("/delete")
async def delete_category(session: Annotated[Session, Depends(get_session)],
                          category_id: int):
    query = select(Category).where(Category.id == category_id)
    category = session.execute(query).scalar()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There is no category found")
    query = update(Category).where(Category.id == category_id).values(is_active=False)
    session.execute(query)
    session.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Category delete is successful'
    }
