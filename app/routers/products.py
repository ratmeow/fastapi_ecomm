from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from app.backend.db_depends import get_session
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import insert, select, update
from slugify import slugify
from starlette import status
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_

from app.schemas import CreateProduct
from app.models.products import Product
from app.models.category import Category

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(session: Annotated[Session, Depends(get_session)]):
    query = select(Product).where(and_(Product.is_active, Product.stock > 0))
    products = session.execute(query).scalars().all()
    if products is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no products")

    return products


@router.post('/create')
async def create_product(session: Annotated[Session, Depends(get_session)], product: CreateProduct):
    query = insert(Product).values(name=product.name,
                                   slug=slugify(product.name),
                                   description=product.description,
                                   price=product.price,
                                   image_url=product.image_url,
                                   stock=product.stock,
                                   rating=0.0,
                                   category_id=product.category)

    session.execute(query)
    session.commit()

    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/{category_slug}')
async def product_by_category(category_slug: str, session: Annotated[Session, Depends(get_session)]):
    category: Category = session.execute(select(Category).where(Category.slug == category_slug)).scalar()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    subcategories = session.execute(select(Category).where(Category.parent_id == category.id)).scalars().all()
    indexes = [category.id] + [cat.id for cat in subcategories]

    products = session.execute(
        select(Product).where(and_(Product.category_id.in_(indexes), Product.stock > 0))).scalars().all()
    return products


@router.get('/detail/{product_slug}')
async def product_detail(product_slug: str, session: Annotated[Session, Depends(get_session)]):
    query = select(Product).where(Product.slug == product_slug)
    product = session.execute(query).scalars().first()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

    return product


@router.put('/detail/{product_slug}')
async def update_product(product_slug: str, session: Annotated[Session, Depends(get_session)],
                         new_product: CreateProduct):
    query = select(Product).where(Product.slug == product_slug)
    product = session.execute(query).scalars().first()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

    query = update(Product).where(Product.slug == product_slug).values(name=new_product.name,
                                                                       description=new_product.description,
                                                                       price=new_product.price,
                                                                       image_url=new_product.image_url,
                                                                       stock=new_product.stock,
                                                                       category_id=new_product.category)

    session.execute(query)
    session.commit()

    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Product update is successful'}


@router.delete('/delete')
async def delete_product(product_slug: str, session: Annotated[Session, Depends(get_session)]):
    query = select(Product).where(Product.slug == product_slug)
    product = session.execute(query).scalars().first()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

    query = update(Product).where(Product.slug == product_slug).values(is_active=False)
    session.execute(query)
    session.commit()

    return {'status_code': status.HTTP_200_OK,
            'transaction': 'Product delete is successful'}
