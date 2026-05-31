"""User schemas — request/response models for user management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.user import UserRole


class UserOut(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    username: str | None = None
    mobile: str
    email: str | None = None
    full_name: str
    role: UserRole
    profile_photo: str | None = None
    is_active: bool
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=15)
    email: str | None = None
    full_name: str = Field(..., min_length=2, max_length=200)
    role: UserRole
    username: str | None = None
    password: str | None = Field(None, min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    profile_photo: str | None = None
    username: str | None = None


class UserListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    role: UserRole | None = None
    search: str | None = None
    is_active: bool | None = None
