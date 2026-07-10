"""
StudyNexs Platform — Async Database Engine & Session Factory
Uses SQLAlchemy 2.0 async with asyncpg driver.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

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


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Dependency: yield a request-scoped async DB session.

    The session is stashed on ``request.state`` so ``CommitOnSuccessRoute`` can COMMIT it
    before the response is sent — committing here (in teardown) would run after the response
    on this FastAPI version, turning a commit-time failure into a silent 2xx with lost data.
    This dependency only rolls back on error; the ``async with`` closes the session on exit.
    """
    async with async_session_factory() as session:
        request.state.db_session = session
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
