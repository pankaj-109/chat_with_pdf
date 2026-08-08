"""Async SQLAlchemy engine, session factory, and table creation."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL
from models import Base

engine = create_async_engine(DATABASE_URL, echo=False)

# expire_on_commit=False keeps ORM objects usable after commit (handy when we
# serialize them into a response right after writing).
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an async DB session (closed on completion)."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables if they do not already exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
