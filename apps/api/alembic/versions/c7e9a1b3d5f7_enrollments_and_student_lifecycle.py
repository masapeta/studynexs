"""enrollments + student lifecycle status (DM-3, expand phase)

students.class_id only knows the CURRENT class; the April year rollover
would overwrite it and destroy per-year history. Add an enrollments table
(one row per student x academic year) and a lifecycle status on students.
Backfill one ACTIVE enrollment per student from the current class_id.
students.class_id stays as the denormalized current pointer.

Revision ID: c7e9a1b3d5f7
Revises: b6d8f0a2c4e6
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c7e9a1b3d5f7"
down_revision = "b6d8f0a2c4e6"
branch_labels = None
depends_on = None

_student_status = postgresql.ENUM(
    "ACTIVE", "TRANSFERRED", "WITHDRAWN", "ALUMNI",
    name="studentstatus", create_type=False,
)
_enrollment_status = postgresql.ENUM(
    "ACTIVE", "PROMOTED", "DETAINED", "TRANSFERRED", "WITHDRAWN", "COMPLETED",
    name="enrollmentstatus", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    _student_status.create(bind, checkfirst=True)
    _enrollment_status.create(bind, checkfirst=True)

    op.add_column(
        "students",
        sa.Column(
            "status",
            _student_status,
            nullable=False,
            server_default="ACTIVE",
        ),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("school_id", sa.UUID(), sa.ForeignKey("schools.id"), nullable=False),
        sa.Column(
            "student_id",
            sa.UUID(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("class_id", sa.UUID(), sa.ForeignKey("classes.id"), nullable=False),
        sa.Column(
            "academic_year_id",
            sa.UUID(),
            sa.ForeignKey("academic_years.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enrollment_status,
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("roll_no", sa.String(length=20), nullable=True),
        sa.Column("enrolled_on", sa.Date(), nullable=True),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.UniqueConstraint(
            "student_id", "academic_year_id", name="uq_enrollment_student_year"
        ),
    )
    op.create_index(
        "ix_enrollments_school_class", "enrollments", ["school_id", "class_id"]
    )
    op.create_index("ix_enrollments_student", "enrollments", ["student_id"])

    # Backfill: one ACTIVE enrollment per student from the current class_id,
    # tied to that class's academic year. Tenant-safe (school_id from the
    # student row); idempotent via NOT EXISTS.
    op.execute(
        """
        INSERT INTO enrollments
            (id, school_id, student_id, class_id, academic_year_id,
             status, roll_no, enrolled_on, created_at)
        SELECT gen_random_uuid(), s.school_id, s.id, s.class_id,
               c.academic_year_id, 'ACTIVE', s.roll_no, s.admission_date, now()
        FROM students s
        JOIN classes c ON c.id = s.class_id
        WHERE NOT EXISTS (
            SELECT 1 FROM enrollments e
            WHERE e.student_id = s.id
              AND e.academic_year_id = c.academic_year_id
        )
        """
    )


def downgrade() -> None:
    op.drop_index("ix_enrollments_student", table_name="enrollments")
    op.drop_index("ix_enrollments_school_class", table_name="enrollments")
    op.drop_table("enrollments")
    op.drop_column("students", "status")
    bind = op.get_bind()
    _enrollment_status.drop(bind, checkfirst=True)
    _student_status.drop(bind, checkfirst=True)
