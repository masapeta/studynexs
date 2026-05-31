"""User API endpoints — CRUD with pagination, admin-only."""
from __future__ import annotations

import math
import uuid

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.rate_limit import rate_limit

settings = get_settings()
from app.core.dependencies import CurrentUser, get_current_user, get_redis, require_roles
from app.modules.users.schemas.user import UserCreate, UserListParams, UserOut, UserUpdate
from app.modules.users.services.user_service import UserService
from app.shared.schemas.common import APIResponse, PaginatedResponse

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[UserOut],
    dependencies=[rate_limit("users:list")],
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """List users for this school (admin only)."""
    params = UserListParams(
        page=page, page_size=page_size, role=role, search=search, is_active=is_active
    )
    service = UserService(db, r)
    users, total = await service.list_users(uuid.UUID(current_user.school_id), params)

    return PaginatedResponse(
        items=[UserOut.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/me", response_model=APIResponse[UserOut])
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile."""
    service = UserService(db)
    user = await service.get_user(uuid.UUID(current_user.school_id), uuid.UUID(current_user.id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(data=UserOut.model_validate(user))


@router.get("/{user_id}", response_model=APIResponse[UserOut])
async def get_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get a user by ID (admin only)."""
    service = UserService(db)
    user = await service.get_user(uuid.UUID(current_user.school_id), user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(data=UserOut.model_validate(user))


@router.post("", response_model=APIResponse[UserOut], status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin only)."""
    service = UserService(db)
    user = await service.create_user(uuid.UUID(current_user.school_id), body)
    return APIResponse(data=UserOut.model_validate(user), message="User created")


@router.patch("/{user_id}", response_model=APIResponse[UserOut])
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """Update a user (admin only)."""
    service = UserService(db, r)
    user = await service.update_user(uuid.UUID(current_user.school_id), user_id, body)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(data=UserOut.model_validate(user), message="User updated")


@router.delete("/{user_id}", response_model=APIResponse)
async def deactivate_user(
    user_id: uuid.UUID,
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin")),
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """Soft-delete (deactivate) a user (admin only)."""
    if str(user_id) == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    service = UserService(db, r)
    user = await service.deactivate_user(uuid.UUID(current_user.school_id), user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(message="User deactivated")
