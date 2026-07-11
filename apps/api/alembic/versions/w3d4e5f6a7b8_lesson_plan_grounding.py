"""Teacher Copilot: curriculum-grounded lesson plans.

Adds provenance to ``lesson_plans`` mirroring question-paper grounding:

- ``pack_id``            nullable FK → curriculum_packs
- ``grounded``           bool, default false (template plans stay valid)
- ``grounding_sources``  JSONB citation sources aligned with segment citations

Revision ID: w3d4e5f6a7b8
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "w3d4e5f6a7b8"
down_revision = "v2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lesson_plans",
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "lesson_plans",
        sa.Column(
            "grounded", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "lesson_plans",
        sa.Column("grounding_sources", postgresql.JSONB(), nullable=True),
    )
    op.create_foreign_key(
        "fk_lesson_plans_pack_id",
        "lesson_plans",
        "curriculum_packs",
        ["pack_id"],
        ["id"],
    )
    op.alter_column("lesson_plans", "grounded", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "fk_lesson_plans_pack_id", "lesson_plans", type_="foreignkey"
    )
    op.drop_column("lesson_plans", "grounding_sources")
    op.drop_column("lesson_plans", "grounded")
    op.drop_column("lesson_plans", "pack_id")
