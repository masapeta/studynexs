"""User service — CRUD with pagination and caching."""
from __future__ import annotations

import math
import uuid

import redis.asyncio as redis
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.modules.users.schemas.user import UserCreate, UserListParams, UserUpdate

settings = get_settings()


class UserService:
    def __init__(self, db: AsyncSession, redis_client: redis.Redis | None = None):
        self.db = db
        self.redis = redis_client

    async def list_users(
        self, school_id: uuid.UUID, params: UserListParams
    ) -> tuple[list[User], int]:
        """Paginated user list with optional role/search filters."""
        query = select(User).where(User.school_id == school_id)

        if params.role:
            query = query.where(User.role == params.role)
        if params.is_active is not None:
            query = query.where(User.is_active == params.is_active)
        if params.search:
            search_term = f"%{params.search}%"
            query = query.where(
                or_(
                    User.full_name.ilike(search_term),
                    User.mobile.ilike(search_term),
                    User.email.ilike(search_term),
                )
            )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (params.page - 1) * params.page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(params.page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_user(self, school_id: uuid.UUID, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, school_id: uuid.UUID, data: UserCreate) -> User:
        user = User(
            school_id=school_id,
            mobile=data.mobile,
            email=data.email,
            full_name=data.full_name,
            role=data.role,
            username=data.username,
            password_hash=hash_password(data.password) if data.password else None,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(
        self, school_id: uuid.UUID, user_id: uuid.UUID, data: UserUpdate
    ) -> User | None:
        user = await self.get_user(school_id, user_id)
        if not user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        await self.db.flush()

        # Invalidate cache
        if self.redis:
            await self.redis.delete(f"{settings.REDIS_USER_CACHE_PREFIX}{user_id}")

        return user

    async def deactivate_user(self, school_id: uuid.UUID, user_id: uuid.UUID) -> User | None:
        user = await self.get_user(school_id, user_id)
        if not user:
            return None
        user.is_active = False
        await self.db.flush()

        if self.redis:
            await self.redis.delete(f"{settings.REDIS_USER_CACHE_PREFIX}{user_id}")

        return user
