from app.backend.db import SessionLocal


async def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
