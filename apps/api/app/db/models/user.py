"""User model — central identity table for all roles."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import BaseModel


class UserRole(str, enum.Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    CLASS_INCHARGE = "class_incharge"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    OPERATIONS = "operations"


class User(BaseModel):
    __tablename__ = "users"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    profile_photo: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    school = relationship("School", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("school_id", "mobile", name="uq_users_school_mobile"),
        UniqueConstraint("school_id", "username", name="uq_users_school_username"),
        Index("ix_users_school_role", "school_id", "role"),
        Index("ix_users_mobile", "mobile"),
    )
