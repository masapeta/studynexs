"""User API endpoints — CRUD with pagination, admin-only."""

from __future__ import annotations

import math
import uuid

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_route import CommitOnSuccessRoute
from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import CurrentUser, get_current_user, get_redis, require_roles
from app.core.pii import mask_mobile
from app.core.rate_limit import rate_limit
from app.core.staff_permissions import get_staff_scope
from app.modules.users.schemas.permissions import UserPermissionsOut
from app.modules.users.schemas.user import UserCreate, UserListParams, UserOut, UserUpdate
from app.modules.users.services.permissions_service import (
    permissions_from_scope,
    portal_permissions,
)
from app.modules.users.services.user_service import UserService, can_assign_role
from app.shared.schemas.common import APIResponse, PaginatedResponse

settings = get_settings()

router = APIRouter(route_class=CommitOnSuccessRoute)


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
    current_user: CurrentUser = Depends(require_roles("admin", "super_admin", "class_incharge")),
    db: AsyncSession = Depends(get_db),
    r: redis.Redis = Depends(get_redis),
):
    """List users for this school (admin + class incharge for staff pickers)."""
    params = UserListParams(
        page=page, page_size=page_size, role=role, search=search, is_active=is_active
    )
    service = UserService(db, r)
    users, total = await service.list_users(uuid.UUID(current_user.school_id), params)

    items = [UserOut.model_validate(u) for u in users]
    # PII minimization: a class incharge uses this list only as a staff picker (names + ids),
    # so it must not become a way to harvest every user's contact details school-wide. Admins
    # keep full visibility; everyone else sees masked mobile and no email.
    if current_user.role not in ("admin", "super_admin"):
        for item in items:
            item.mobile = mask_mobile(item.mobile) or ""
            item.email = None

    return PaginatedResponse(
        items=items,
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


@router.get("/me/permissions", response_model=APIResponse[UserPermissionsOut])
async def get_my_permissions(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Feature and class-scope permissions for the current user (drives admin-web RBAC)."""
    if current_user.role in ("parent", "student"):
        return APIResponse(data=portal_permissions(current_user.role))
    scope = await get_staff_scope(db, current_user)
    return APIResponse(data=permissions_from_scope(scope))


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
    # Role ceiling: an admin cannot mint a super_admin (or any role above its own).
    if not can_assign_role(current_user.role, body.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign a role higher than your own.",
        )
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
    target = await service.get_user(uuid.UUID(current_user.school_id), user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    # Role ceiling applies to the TARGET's current role too — an admin must not be able to edit
    # a principal (super_admin) just because they aren't changing the role field.
    if not can_assign_role(current_user.role, target.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot modify a user whose role is higher than your own.",
        )
    if body.role is not None and not can_assign_role(current_user.role, body.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot assign a role higher than your own.",
        )
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
    target = await service.get_user(uuid.UUID(current_user.school_id), user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    # Ceiling: can't deactivate a user who outranks you (an admin can't disable a principal).
    if not can_assign_role(current_user.role, target.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot deactivate a user whose role is higher than your own.",
        )
    user = await service.deactivate_user(uuid.UUID(current_user.school_id), user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return APIResponse(message="User deactivated")
