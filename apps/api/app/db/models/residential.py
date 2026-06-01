"""Residential / hostel models — blocks and student room allocations."""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import BaseModel


class BlockGender(str, enum.Enum):
    BOYS = "boys"
    GIRLS = "girls"
    MIXED = "mixed"


class ResidentialBlock(BaseModel):
    __tablename__ = "residential_blocks"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    block_name: Mapped[str] = mapped_column(String(100), nullable=False)
    block_gender: Mapped[BlockGender] = mapped_column(
        Enum(BlockGender), default=BlockGender.MIXED, nullable=False
    )
    warden_name: Mapped[str | None] = mapped_column(String(100))
    warden_contact: Mapped[str | None] = mapped_column(String(15))
    total_rooms: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (Index("ix_residential_blocks_school", "school_id"),)


class RoomAllocation(BaseModel):
    __tablename__ = "room_allocations"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    block_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("residential_blocks.id"), nullable=False
    )
    room_number: Mapped[str | None] = mapped_column(String(20))

    __table_args__ = (Index("ix_room_allocations_block", "block_id"),)
