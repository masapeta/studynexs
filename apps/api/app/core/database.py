"""
StudyNexs Platform — Async Database Engine & Session Factory
Uses SQLAlchemy 2.0 async with asyncpg driver.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Environment, get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yields an async DB session, auto-closes on exit."""
    async with async_session_factory() as session:
        try:
            yield session
            if settings.ENVIRONMENT != Environment.TESTING:
                await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            if settings.ENVIRONMENT != Environment.TESTING:
                await session.close()
