from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session, create_session
from sqlalchemy import create_engine

from app.backend.config import settings

# engine = create_async_engine(settings.PG_URL)
# session = async_sessionmaker(bind=engine, expire_on_commit=False)

engine = create_engine(settings.PG_URL)
SessionLocal = sessionmaker(engine)


class Base(DeclarativeBase):
    pass
