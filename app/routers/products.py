from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from app.backend.db_depends import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from slugify import slugify
from starlette import status
from sqlalchemy.sql import and_

from app.routers.auth import get_current_user
from app.schemas import CreateProduct
from app.models.products import Product
from app.models.category import Category

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(session: Annotated[AsyncSession, Depends(get_session)]):
    query = await session.execute(select(Product).where(and_(Product.is_active, Product.stock > 0)))
    products = query.scalars().all()
    if products is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no products")

    return products


@router.post('/create')
async def create_product(session: Annotated[AsyncSession, Depends(get_session)], product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        query = insert(Product).values(name=product.name,
                                       slug=slugify(product.name),
                                       description=product.description,
                                       price=product.price,
                                       image_url=product.image_url,
                                       stock=product.stock,
                                       rating=0.0,
                                       category_id=product.category,
                                       supplied_id=get_user.get("id"))

        await session.execute(query)
        await session.commit()

        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.get('/{category_slug}')
async def product_by_category(category_slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    category = await session.scalar(select(Category).where(Category.slug == category_slug))
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    subcategories_cor = await session.scalars(select(Category).where(Category.parent_id == category.id))
    subcategories = subcategories_cor.all()
    indexes = [category.id] + [cat.id for cat in subcategories]

    products = await session.scalars(
        select(Product).where(and_(Product.category_id.in_(indexes), Product.stock > 0)))
    return products.all()


@router.get('/detail/{product_slug}')
async def product_detail(product_slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    query = select(Product).where(Product.slug == product_slug)
    product_cor = await session.scalars(query)
    product = product_cor.first()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

    return product


@router.put('/detail/{product_slug}')
async def update_product(product_slug: str, session: Annotated[AsyncSession, Depends(get_session)],
                         new_product: CreateProduct,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        query = select(Product).where(Product.slug == product_slug)
        product_cor = await session.scalars(query)
        product = product_cor.first()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

        query = update(Product).where(Product.slug == product_slug).values(name=new_product.name,
                                                                           description=new_product.description,
                                                                           price=new_product.price,
                                                                           image_url=new_product.image_url,
                                                                           stock=new_product.stock,
                                                                           category_id=new_product.category)

        await session.execute(query)
        await session.commit()

        return {'status_code': status.HTTP_200_OK,
                'transaction': 'Product update is successful'}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.delete('/delete')
async def delete_product(product_slug: str, session: Annotated[AsyncSession, Depends(get_session)],
                         get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin") or get_user.get("is_supplier"):
        query = select(Product).where(Product.slug == product_slug)
        product_cor = await session.scalars(query)
        product = product_cor.first()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

        query = update(Product).where(Product.slug == product_slug).values(is_active=False)
        await session.execute(query)
        await session.commit()

        return {'status_code': status.HTTP_200_OK,
                'transaction': 'Product delete is successful'}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )
