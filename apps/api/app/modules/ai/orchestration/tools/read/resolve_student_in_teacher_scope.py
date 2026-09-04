"""Resolve a student selector within the authenticated teacher scope."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.staff_permissions import get_staff_scope
from app.db.models.academic import Class
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.ai.gateway.input_guard import sanitize_prompt_text
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext, WorkspaceToolMetadata
from app.modules.ai.orchestration.tools.read._shared import current_user_from_context
from app.modules.workspace.schemas.blocks import StudentCardPayload, WorkspaceSchemaModel


class ResolveStudentInTeacherScopeInput(WorkspaceSchemaModel):
    selector: str = Field(..., strict=True, min_length=1, max_length=120)

    @field_validator("selector")
    @classmethod
    def _sanitize_selector(cls, value: str) -> str:
        cleaned = sanitize_prompt_text(value, max_length=120, field_name="selector")
        if not cleaned:
            raise ValueError("selector is required")
        return cleaned


class ResolveStudentCandidate(StudentCardPayload):
    pass


class ResolveStudentInTeacherScopeOutput(WorkspaceSchemaModel):
    status: Literal["resolved", "ambiguous", "forbidden", "not_found"]
    student_id: str | None = None
    display_name: str | None = None
    class_label: str | None = None
    section_label: str | None = None
    admission_no: str | None = None
    resolution_method: Literal["exact", "alias", "admission_no"] | None = None
    verified_scope: bool = False
    matches: list[ResolveStudentCandidate] = Field(default_factory=list)
    detail: str | None = None


def _normalize(value: str | None) -> str:
    return (value or "").strip().casefold()


def _candidate_from_row(row: tuple[Student, str, str, str]) -> ResolveStudentCandidate:
    student, full_name, grade, section = row
    return ResolveStudentCandidate(
        student_id=str(student.id),
        display_name=full_name,
        class_label=grade,
        section_label=section,
        admission_no=student.admission_no,
    )


def _resolved_output(
    row: tuple[Student, str, str, str],
    *,
    resolution_method: Literal["exact", "alias", "admission_no"],
) -> ResolveStudentInTeacherScopeOutput:
    candidate = _candidate_from_row(row)
    return ResolveStudentInTeacherScopeOutput(
        status="resolved",
        student_id=candidate.student_id,
        display_name=candidate.display_name,
        class_label=candidate.class_label,
        section_label=candidate.section_label,
        admission_no=candidate.admission_no,
        resolution_method=resolution_method,
        verified_scope=True,
    )


async def _query_matches(
    db: AsyncSession,
    *,
    school_id: uuid.UUID,
    selector: str,
    query_type: Literal["admission_no", "exact_name", "roll_no", "alias_name"],
) -> list[tuple[Student, str, str, str]]:
    stmt = (
        select(Student, User.full_name, Class.grade, Class.section)
        .join(User, User.id == Student.user_id)
        .join(Class, Class.id == Student.class_id)
        .where(Student.school_id == school_id)
        .limit(10)
    )

    normalized = _normalize(selector)
    if query_type == "admission_no":
        stmt = stmt.where(Student.admission_no.ilike(selector))
    elif query_type == "exact_name":
        stmt = stmt.where(User.full_name.ilike(selector))
    elif query_type == "roll_no":
        stmt = stmt.where(Student.roll_no == selector)
    else:
        stmt = stmt.where(User.full_name.ilike(f"%{selector}%"))

    rows = (await db.execute(stmt)).all()
    if query_type in {"admission_no", "exact_name"}:
        rows = [
            row
            for row in rows
            if _normalize(
                row[1] if query_type == "exact_name" else row[0].admission_no
            )
            == normalized
        ]
    return rows


async def resolve_student_in_teacher_scope(
    db: AsyncSession,
    context: WorkspaceToolContext,
    payload: ResolveStudentInTeacherScopeInput,
) -> ResolveStudentInTeacherScopeOutput:
    current_user = current_user_from_context(context)
    scope = await get_staff_scope(db, current_user)

    for query_type, resolution_method in (
        ("admission_no", "admission_no"),
        ("exact_name", "exact"),
        ("roll_no", "alias"),
        ("alias_name", "alias"),
    ):
        school_matches = await _query_matches(
            db,
            school_id=context.school_id,
            selector=payload.selector,
            query_type=query_type,
        )
        if not school_matches:
            continue
        accessible_matches = [
            row for row in school_matches if scope.can_access_class(row[0].class_id)
        ]
        if not accessible_matches:
            return ResolveStudentInTeacherScopeOutput(
                status="forbidden",
                verified_scope=False,
                detail="The matched student is outside your assigned classes.",
            )
        if len(accessible_matches) > 1:
            return ResolveStudentInTeacherScopeOutput(
                status="ambiguous",
                verified_scope=False,
                matches=[_candidate_from_row(row) for row in accessible_matches],
                detail="Multiple students matched that selector. Refine the request.",
            )
        return _resolved_output(
            accessible_matches[0],
            resolution_method=resolution_method,
        )

    return ResolveStudentInTeacherScopeOutput(
        status="not_found",
        verified_scope=False,
        detail="No student matched that selector in your school.",
    )


TOOL_METADATA = WorkspaceToolMetadata(
    name="resolve_student_in_teacher_scope",
    input_schema=ResolveStudentInTeacherScopeInput,
    output_schema=ResolveStudentInTeacherScopeOutput,
    allowed_roles=["teacher", "class_incharge"],
    scope_rule="school-scoped lookup with existing teacher/class-incharge access checks",
    audit_event_type="workspace.read.resolve_student_in_teacher_scope",
    pii_level="medium",
    max_payload_size=512,
    tool_result_cache_policy="per_turn",
    timeout_ms=500,
    retry_count=1,
    circuit_breaker_threshold=3,
    circuit_breaker_cooldown_seconds=60,
)
TOOL_HANDLER = resolve_student_in_teacher_scope
