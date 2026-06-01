"""add residential blocks + room allocations

Revision ID: c9f1e3a5d7b2
Revises: b8e0d2f4a6c1
Create Date: 2026-06-01

Residential / hostel module: blocks (with warden + gender) and student room allocations.
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "c9f1e3a5d7b2"
down_revision: Union[str, None] = "b8e0d2f4a6c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "residential_blocks",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("block_name", sa.String(length=100), nullable=False),
        sa.Column(
            "block_gender",
            sa.Enum("BOYS", "GIRLS", "MIXED", name="blockgender"),
            nullable=False,
        ),
        sa.Column("warden_name", sa.String(length=100), nullable=True),
        sa.Column("warden_contact", sa.String(length=15), nullable=True),
        sa.Column("total_rooms", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_residential_blocks_school", "residential_blocks", ["school_id"])

    op.create_table(
        "room_allocations",
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("block_id", sa.UUID(), nullable=False),
        sa.Column("room_number", sa.String(length=20), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["block_id"], ["residential_blocks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_room_allocations_block", "room_allocations", ["block_id"])


def downgrade() -> None:
    op.drop_index("ix_room_allocations_block", table_name="room_allocations")
    op.drop_table("room_allocations")
    op.drop_index("ix_residential_blocks_school", table_name="residential_blocks")
    op.drop_table("residential_blocks")
    sa.Enum(name="blockgender").drop(op.get_bind(), checkfirst=True)
