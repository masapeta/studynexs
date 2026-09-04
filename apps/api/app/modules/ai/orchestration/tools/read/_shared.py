"""Shared helpers for bounded Phase 0 read tools."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.academic import Class
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext
from app.modules.workspace.schemas.blocks import StudentCardPayload


def current_user_from_context(context: WorkspaceToolContext) -> CurrentUser:
    return CurrentUser(
        id=str(context.teacher_user_id),
        school_id=str(context.school_id),
        role=context.role,
        tenant_slug=context.tenant_slug,
        full_name="",
        mobile="",
        is_active=True,
        jti=context.correlation_id or "workspace-tool",
        sid="",
    )


async def load_student_card_payload(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    student_id: uuid.UUID,
) -> StudentCardPayload | None:
    row = (
        await db.execute(
            select(Student.id, Student.admission_no, User.full_name, Class.grade, Class.section)
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(Student.school_id == school_id, Student.id == student_id)
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    student_pk, admission_no, full_name, grade, section = row
    return StudentCardPayload(
        student_id=str(student_pk),
        display_name=full_name,
        class_label=grade,
        section_label=section,
        admission_no=admission_no,
    )
