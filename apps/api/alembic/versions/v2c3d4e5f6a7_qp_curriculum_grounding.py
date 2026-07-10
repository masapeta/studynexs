"""Assessment Intelligence: curriculum-grounded question papers.

Adds provenance to `question_papers` so a paper can be traced to the APPROVED CurriculumPack
it was grounded on (via RAG retrieval):

- ``pack_id``            nullable FK → curriculum_packs (which pack grounded this paper)
- ``grounded``           bool, default false (legacy/free-text papers stay valid, grounded=False)
- ``grounding_sources``  JSONB, ordered citation sources aligned with per-question ``citations``
                         indices: [{"index", "chapter", "topic", "ref_id"}]

Per-question metadata (bloom / difficulty / learning_outcome / concepts / citations) lives inside
the existing ``sections`` JSONB, so no column is needed for it. Additive + reversible.

Revision ID: v2c3d4e5f6a7
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "v2c3d4e5f6a7"
down_revision = "u1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "question_papers",
        sa.Column("pack_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "question_papers",
        sa.Column(
            "grounded", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.add_column(
        "question_papers",
        sa.Column("grounding_sources", postgresql.JSONB(), nullable=True),
    )
    op.create_foreign_key(
        "fk_question_papers_pack_id",
        "question_papers",
        "curriculum_packs",
        ["pack_id"],
        ["id"],
    )
    # Drop the server_default now that existing rows are backfilled to false — new rows get
    # their value from the model (default=False), keeping the column app-managed.
    op.alter_column("question_papers", "grounded", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "fk_question_papers_pack_id", "question_papers", type_="foreignkey"
    )
    op.drop_column("question_papers", "grounding_sources")
    op.drop_column("question_papers", "grounded")
    op.drop_column("question_papers", "pack_id")
