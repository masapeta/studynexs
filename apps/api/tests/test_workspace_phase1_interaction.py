import pytest
import uuid
from sqlalchemy import select
from app.db.models.mastery import MasteryFlag, FlagStatus
from app.modules.workspace.services.workspace_service import WorkspaceService
from app.modules.workspace.schemas.request import WorkspaceTurnRequest
from app.modules.ai.orchestration.tool_registry import WorkspaceToolRegistry

@pytest.mark.asyncio
async def test_mark_evidence_as_reviewed_tool_executes(db_session, teacher_user, test_school, test_class, student_user):
    # 1. Seed a flag
    flag = MasteryFlag(
        school_id=test_school.id,
        student_id=student_user.id,
        class_id=test_class.id,
        subject_id=uuid.uuid4(),
        academic_year_id=uuid.uuid4(),
        topic="Maths",
        topic_display="Maths",
        severity="medium",
        status=FlagStatus.PENDING_REVIEW,
    )
    db_session.add(flag)
    await db_session.flush()

    # 2. Invoke tool via orchestrator
    registry = WorkspaceToolRegistry.load_default(include_write_tools=True)
    service = WorkspaceService(db_session, registry)
    
    # 3. Simulate tool call
    result = await service.handle_turn(
        teacher_user.id, 
        WorkspaceTurnRequest(mode='read', text=f"Exec mark_evidence_as_reviewed {flag.id}")
    )
    
    # 4. Assert updated
    await db_session.refresh(flag)
    assert flag.status == FlagStatus.APPROVED
    assert flag.reviewed_by == teacher_user.id
