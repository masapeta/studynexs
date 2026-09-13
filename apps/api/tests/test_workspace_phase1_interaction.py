from __future__ import annotations

import pytest

from app.db.models.mastery import FlagStatus
from app.modules.ai.orchestration.tool_registry import WorkspaceToolRegistry
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext
from app.modules.ai.orchestration.write_orchestrator import WorkspaceWriteOrchestrator
from tests.test_workspace_tool_registry import _seed_grounded_flagging_report


@pytest.mark.asyncio
async def test_mark_evidence_as_reviewed_tool_executes(
    client,
    db_session,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
):
    _weak, _subject, flag, _evaluation = await _seed_grounded_flagging_report(
        client,
        db_session,
        admin_user=admin_user,
        teacher_user=teacher_user,
        student_user=student_user,
        test_school=test_school,
        test_class=test_class,
    )

    registry = WorkspaceToolRegistry.load_default(include_write_tools=True)
    orchestrator = WorkspaceWriteOrchestrator(registry)
    context = WorkspaceToolContext(
        teacher_user_id=teacher_user.id,
        school_id=test_school.id,
        role="teacher",
        tenant_slug="test",
    )

    tool_result = await orchestrator.execute(
        db_session,
        context=context,
        tool_name="mark_evidence_as_reviewed",
        payload={"flag_id": str(flag.id)},
    )

    assert tool_result["status"] == "reviewed"

    await db_session.refresh(flag)
    assert flag.status == FlagStatus.APPROVED
    assert flag.reviewed_by == teacher_user.id
