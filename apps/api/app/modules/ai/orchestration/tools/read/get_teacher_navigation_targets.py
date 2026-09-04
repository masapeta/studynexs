"""Return safe existing teaching routes for the Phase 0 workspace."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.staff_permissions import get_staff_scope
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext, WorkspaceToolMetadata
from app.modules.ai.orchestration.tools.read._shared import current_user_from_context
from app.modules.users.services.permissions_service import permissions_from_scope
from app.modules.workspace.schemas.blocks import WorkspaceAction, WorkspaceSchemaModel

_TEACHING_ROOT = "/dashboard/teaching"
_TEACHING_EXAMS = "/dashboard/teaching/exams"
_TEACHING_GRADEBOOK = "/dashboard/teaching/gradebook"
_TEACHING_REPORT_CARDS = "/dashboard/teaching/report-cards"
_TEACHING_MASTERY = "/dashboard/teaching/mastery"


class GetTeacherNavigationTargetsInput(WorkspaceSchemaModel):
    student_id: uuid.UUID


class GetTeacherNavigationTargetsOutput(WorkspaceSchemaModel):
    status: Literal["ok", "forbidden", "not_found"]
    actions: list[WorkspaceAction] = Field(default_factory=list)
    detail: str | None = None


async def get_teacher_navigation_targets(
    db: AsyncSession,
    context: WorkspaceToolContext,
    payload: GetTeacherNavigationTargetsInput,
) -> GetTeacherNavigationTargetsOutput:
    current_user = current_user_from_context(context)
    try:
        await assert_can_access_student(current_user, db, payload.student_id)
    except Exception as exc:  # noqa: BLE001
        detail = getattr(exc, "detail", "Access denied")
        status = "not_found" if getattr(exc, "status_code", None) == 404 else "forbidden"
        return GetTeacherNavigationTargetsOutput(status=status, detail=detail)

    scope = await get_staff_scope(db, current_user)
    perms = permissions_from_scope(scope)
    actions = [
        WorkspaceAction(
            label="Open teaching hub",
            href=_TEACHING_ROOT,
            permission_gate="can_use_exams",
            enabled=perms.can_use_exams,
        ),
        WorkspaceAction(
            label="Open mastery",
            href=_TEACHING_MASTERY,
            permission_gate="can_use_mastery",
            enabled=perms.can_use_mastery,
        ),
        WorkspaceAction(
            label="Open exams",
            href=_TEACHING_EXAMS,
            permission_gate="can_use_exams",
            enabled=perms.can_use_exams,
        ),
        WorkspaceAction(
            label="Open gradebook",
            href=_TEACHING_GRADEBOOK,
            permission_gate="can_use_exams",
            enabled=perms.can_use_exams,
        ),
        WorkspaceAction(
            label="Open report cards",
            href=_TEACHING_REPORT_CARDS,
            permission_gate="can_use_report_cards",
            enabled=perms.can_use_report_cards,
        ),
    ]
    return GetTeacherNavigationTargetsOutput(status="ok", actions=actions)


TOOL_METADATA = WorkspaceToolMetadata(
    name="get_teacher_navigation_targets",
    input_schema=GetTeacherNavigationTargetsInput,
    output_schema=GetTeacherNavigationTargetsOutput,
    allowed_roles=["teacher", "class_incharge"],
    scope_rule="student access check plus existing teaching permission gates",
    audit_event_type="workspace.read.get_teacher_navigation_targets",
    pii_level="low",
    max_payload_size=256,
    tool_result_cache_policy="short_ttl",
    timeout_ms=400,
    retry_count=0,
    circuit_breaker_threshold=3,
    circuit_breaker_cooldown_seconds=60,
)
TOOL_HANDLER = get_teacher_navigation_targets
