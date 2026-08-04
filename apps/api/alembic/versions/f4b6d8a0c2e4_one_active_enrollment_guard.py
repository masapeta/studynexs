"""One ACTIVE enrollment per student — partial unique index

uq_enrollment_student_year allows one enrollment per student per YEAR, but
nothing stopped a student holding ACTIVE rows in two different years. The
lifecycle service resolves "the current enrollment" with scalar_one_or_none(),
so a duplicate-ACTIVE anomaly would surface as MultipleResultsFound — a 500 on
the student page and a blocked promotion. Enforce the invariant at the
database, the same way uq_one_active_year_per_school guards academic years.

Safety: verified zero students with more than one ACTIVE enrollment before
authoring; a violation would abort this migration loudly rather than hide.

Revision ID: f4b6d8a0c2e4
Revises: e2a4c6d8f0b2
"""
from __future__ import annotations

from alembic import op

revision = "f4b6d8a0c2e4"
down_revision = "e2a4c6d8f0b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_one_active_enrollment_per_student",
        "enrollments",
        ["student_id"],
        unique=True,
        postgresql_where="status = 'ACTIVE'",
    )


def downgrade() -> None:
    op.drop_index(
        "uq_one_active_enrollment_per_student",
        table_name="enrollments",
    )
