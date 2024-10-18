from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from app.backend.db_depends import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from slugify import slugify
from starlette import status
from sqlalchemy.sql import and_

from app.routers.auth import get_current_user
from app.schemas import CreateProduct, CreateReview
from app.models.reviews import Review
from app.models.rating import Rating
from app.models.products import Product

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/')
async def all_reviews(session: Annotated[AsyncSession, Depends(get_session)]):
    query = await session.execute(select(Review).where(Review.is_active))
    reviews = query.scalars().all()
    if reviews is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no products")

    return reviews


@router.post('/create')
async def add_review(session: Annotated[AsyncSession, Depends(get_session)], review: CreateReview,
                     get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_customer"):

        product: Product = await session.scalar(select(Product).where(Product.slug == review.product_slug))

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

        rating: Rating = await session.scalar(insert(Rating).values(grade=review.grade,
                                                                    user_id=get_user.get("id"),
                                                                    product_id=product.id).returning(Rating))

        await session.execute(insert(Review).values(user_id=get_user.get("id"),
                                                    product_id=product.id,
                                                    rating_id=rating.id,
                                                    comment=review.comment))

        product_rating = list(await session.scalars(select(Rating.grade).where(Rating.product_id == int(product.id))))
        new_grade = sum(product_rating) / len(product_rating)

        await session.execute(update(Product).where(Product.id == int(product.id)).values(rating=new_grade))

        await session.commit()

        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not customer!'
        )


@router.get('/{product_slug}')
async def product_detail(product_slug: str, session: Annotated[AsyncSession, Depends(get_session)]):
    product: Product = await session.scalar(select(Product).where(Product.slug == product_slug))

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

    ratings = await session.scalars(select(Rating).where(Rating.product_id == int(product.id)))
    reviews = await session.scalars(select(Review).where(Review.product_id == int(product.id)))

    return {"reviews": reviews.all(),
            "ratings": ratings.all()}


@router.delete('/delete')
async def delete_review(product_slug: str, session: Annotated[AsyncSession, Depends(get_session)],
                        get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get("is_admin"):
        product: Product = await session.scalar(select(Product).where(Product.slug == product_slug))

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="There are no product")

        await session.execute(update(Rating).where(Rating.product_id == int(product.id)).values(is_active=False))
        await session.execute(update(Review).where(Review.product_id == int(product.id)).values(is_active=False))

        await session.commit()

        return {'status_code': status.HTTP_200_OK,
                'transaction': 'Review delete is successful'}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not admin!'
        )
