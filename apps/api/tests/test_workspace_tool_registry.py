from __future__ import annotations

import pytest
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models.academic import Subject, TeacherSubjectMapping
from app.db.models.answer_sheet_evaluation import EVAL_STATUS_APPROVED, AnswerSheetEvaluation
from app.db.models.audit import AuditLog
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.examination import Exam
from app.db.models.knowledge_graph import ConceptSource, CurriculumConcept
from app.db.models.mastery import MasteryFlag
from app.db.models.question_paper import PaperStatus, QuestionPaper
from app.db.models.student import Enrollment, Student
from app.db.models.user import User, UserRole
from app.modules.ai.orchestration.tool_registry import (
    RegisteredWorkspaceTool,
    WorkspaceToolCircuitOpenError,
    WorkspaceToolExecutionError,
    WorkspaceToolRegistry,
)
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext, WorkspaceToolMetadata
from app.modules.mastery.services.mastery_service import recompute_class_subject
from tests.test_mastery_api import _flag_of
from tests.test_mastery_flags import _seed_flagging_scenario


def _context(*, teacher_user: User, role: str = "teacher") -> WorkspaceToolContext:
    return WorkspaceToolContext(
        teacher_user_id=teacher_user.id,
        school_id=teacher_user.school_id,
        role=role,
        tenant_slug="test",
        correlation_id="workspace-test",
    )


async def _seed_grounded_flagging_report(
    client,
    db_session,
    *,
    admin_user: User,
    teacher_user: User,
    student_user: User,
    test_school,
    test_class,
) -> tuple[Student, Subject, MasteryFlag, AnswerSheetEvaluation]:
    from datetime import datetime, timezone

    weak, subject, _token = await _seed_flagging_scenario(
        client,
        db_session,
        test_school,
        test_class,
        student_user,
    )
    flag = await _flag_of(db_session, weak.id)
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=subject.id,
            class_id=test_class.id,
            is_primary=True,
        )
    )

    pack = CurriculumPack(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        academic_year_id=test_class.academic_year_id,
        board="SSC",
        book_title="Maths",
        version=1,
        status=PackStatus.APPROVED,
        created_by=admin_user.id,
        approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
        rag_indexed_at=datetime.now(timezone.utc),
        rag_index_topic_count=1,
    )
    db_session.add(pack)
    await db_session.flush()
    chapter = CurriculumChapter(
        school_id=test_school.id,
        pack_id=pack.id,
        number="1",
        title="Algebra",
        order_index=1,
    )
    db_session.add(chapter)
    await db_session.flush()
    topic = CurriculumTopic(
        school_id=test_school.id,
        chapter_id=chapter.id,
        title="Algebra",
        order_index=1,
        concepts=["Linear equations"],
    )
    db_session.add(topic)
    await db_session.flush()
    db_session.add(
        CurriculumConcept(
            school_id=test_school.id,
            pack_id=pack.id,
            topic_id=topic.id,
            slug="linear-equations",
            title="Linear equations",
            order_index=1,
            source=ConceptSource.PACK_JSONB,
        )
    )
    paper = QuestionPaper(
        school_id=test_school.id,
        class_id=test_class.id,
        subject_id=subject.id,
        created_by=admin_user.id,
        pack_id=pack.id,
        grounded=True,
        grounding_sources=[{"index": 1, "chapter": "Algebra", "topic": "Algebra"}],
        title="Algebra Evidence Paper",
        board="SSC",
        grade=test_class.grade,
        subject_name=subject.name,
        total_marks=25,
        topics=["Algebra"],
        sections=[],
        status=PaperStatus.APPROVED,
        approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(paper)
    await db_session.flush()

    exams = list(
        (
            await db_session.execute(
                select(Exam).where(
                    Exam.school_id == test_school.id,
                    Exam.class_id == test_class.id,
                    Exam.subject_id == subject.id,
                )
            )
        )
        .scalars()
        .all()
    )
    for exam in exams:
        exam.source_paper_id = paper.id

    evaluation = AnswerSheetEvaluation(
        school_id=test_school.id,
        exam_id=exams[0].id,
        student_id=weak.id,
        created_by=admin_user.id,
        status=EVAL_STATUS_APPROVED,
        ai_suggestions={"1": {"marks_suggested": 2, "max_marks": 5}},
        approved_by=admin_user.id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(evaluation)
    await db_session.flush()
    await recompute_class_subject(db_session, test_school.id, test_class.id, subject.id)
    return weak, subject, flag, evaluation


@pytest.mark.asyncio
async def test_workspace_registry_loads_exact_phase0_tools():
    registry = WorkspaceToolRegistry.load_default()

    assert registry.names() == (
        "resolve_student_in_teacher_scope",
        "get_student_learning_evidence_report",
        "get_teacher_navigation_targets",
    )
    assert [tool.read_only for tool in registry.definitions()] == [True, True, True]


@pytest.mark.asyncio
async def test_workspace_registry_retries_once_then_opens_circuit(db_session, teacher_user):
    class DummyInput(BaseModel):
        value: int

    class DummyOutput(BaseModel):
        value: int

    attempts = {"count": 0}
    clock = {"now": 100.0}

    async def flaky_handler(_db, _context, payload):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ConnectionError("temporary")
        return DummyOutput(value=payload.value)

    async def failing_handler(_db, _context, _payload):
        raise ConnectionError("down")

    metadata = WorkspaceToolMetadata(
        name="test_tool",
        input_schema=DummyInput,
        output_schema=DummyOutput,
        allowed_roles=["teacher"],
        scope_rule="test",
        audit_event_type="workspace.test",
        pii_level="none",
        max_payload_size=128,
        tool_result_cache_policy="no_cache",
        timeout_ms=50,
        retry_count=1,
        circuit_breaker_threshold=2,
        circuit_breaker_cooldown_seconds=30,
    )
    context = _context(teacher_user=teacher_user)

    registry = WorkspaceToolRegistry.from_tools(
        (RegisteredWorkspaceTool(metadata=metadata, handler=flaky_handler),),
        strict_approved_names=False,
        clock=lambda: clock["now"],
    )
    result = await registry.execute(
        "test_tool",
        db=db_session,
        context=context,
        payload={"value": 7},
    )
    assert result.value == 7
    assert attempts["count"] == 2

    failing_registry = WorkspaceToolRegistry.from_tools(
        (RegisteredWorkspaceTool(metadata=metadata, handler=failing_handler),),
        strict_approved_names=False,
        clock=lambda: clock["now"],
    )
    with pytest.raises(WorkspaceToolExecutionError):
        await failing_registry.execute(
            "test_tool",
            db=db_session,
            context=context,
            payload={"value": 7},
        )
    with pytest.raises(WorkspaceToolExecutionError):
        await failing_registry.execute(
            "test_tool",
            db=db_session,
            context=context,
            payload={"value": 7},
        )
    with pytest.raises(WorkspaceToolCircuitOpenError):
        await failing_registry.execute(
            "test_tool",
            db=db_session,
            context=context,
            payload={"value": 7},
        )


@pytest.mark.asyncio
async def test_resolve_student_in_teacher_scope_returns_ambiguity(
    db_session,
    teacher_user,
    test_school,
    test_class,
    student_user,
):
    from app.core.security import hash_password
    from app.modules.ai.orchestration.tools.read.resolve_student_in_teacher_scope import (
        ResolveStudentInTeacherScopeInput,
    )

    test_class.class_incharge_id = teacher_user.id

    duplicate_user = User(
        school_id=test_school.id,
        username="second_student",
        mobile="+919876543250",
        full_name="Test Student",
        role=UserRole.STUDENT,
        password_hash=hash_password("Student@123"),
        is_active=True,
    )
    db_session.add(duplicate_user)
    await db_session.flush()
    duplicate_student = Student(
        school_id=test_school.id,
        user_id=duplicate_user.id,
        class_id=test_class.id,
        admission_no="ADM002",
        roll_no="2",
    )
    db_session.add(duplicate_student)
    await db_session.flush()
    db_session.add(
        Enrollment(
            school_id=test_school.id,
            student_id=duplicate_student.id,
            class_id=test_class.id,
            academic_year_id=test_class.academic_year_id,
        )
    )
    await db_session.flush()

    registry = WorkspaceToolRegistry.load_default()
    result = await registry.execute(
        "resolve_student_in_teacher_scope",
        db=db_session,
        context=_context(teacher_user=teacher_user),
        payload=ResolveStudentInTeacherScopeInput(selector="Test Student"),
    )
    assert result.status == "ambiguous"
    assert len(result.matches) == 2


@pytest.mark.asyncio
async def test_learning_evidence_report_returns_grounded_deterministic_payload(
    client,
    db_session,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
):
    weak, subject, _flag, evaluation = await _seed_grounded_flagging_report(
        client,
        db_session,
        admin_user=admin_user,
        teacher_user=teacher_user,
        student_user=student_user,
        test_school=test_school,
        test_class=test_class,
    )
    registry = WorkspaceToolRegistry.load_default()

    result = await registry.execute(
        "get_student_learning_evidence_report",
        db=db_session,
        context=_context(teacher_user=teacher_user),
        payload={"student_id": str(weak.id)},
    )
    assert result.status == "ok"
    assert result.student.display_name == "Test Student"
    assert result.verification_status == "verified"
    assert result.summary_metrics.items[1].value >= 1
    assert result.recent_assessment_evidence.rows
    assert any(citation.source_id == str(evaluation.id) for citation in result.citations)

    audit_entry = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == "workspace.read.get_student_learning_evidence_report",
                AuditLog.resource_id == "get_student_learning_evidence_report",
            )
        )
    ).scalars().first()
    assert audit_entry is not None
    assert audit_entry.school_id == test_school.id
    assert audit_entry.user_id == teacher_user.id
    assert audit_entry.resource_type == "workspace_tool"
    assert audit_entry.details["outcome"] == "success"
    assert audit_entry.details["tool_name"] == "get_student_learning_evidence_report"
    assert audit_entry.details["attempt_count"] == 1
    assert audit_entry.details["correlation_id"] == "workspace-test"


@pytest.mark.asyncio
async def test_workspace_registry_audits_failed_tool_execution(db_session, teacher_user):
    class DummyInput(BaseModel):
        value: int

    class DummyOutput(BaseModel):
        value: int

    async def failing_handler(_db, _context, _payload):
        raise ConnectionError("down")

    metadata = WorkspaceToolMetadata(
        name="test_tool",
        input_schema=DummyInput,
        output_schema=DummyOutput,
        allowed_roles=["teacher"],
        scope_rule="test",
        audit_event_type="workspace.test",
        pii_level="none",
        max_payload_size=128,
        tool_result_cache_policy="no_cache",
        timeout_ms=50,
        retry_count=1,
        circuit_breaker_threshold=2,
        circuit_breaker_cooldown_seconds=30,
    )
    context = WorkspaceToolContext(
        teacher_user_id=teacher_user.id,
        school_id=teacher_user.school_id,
        role="teacher",
        tenant_slug="test",
        correlation_id="workspace-test-failure",
    )
    registry = WorkspaceToolRegistry.from_tools(
        (RegisteredWorkspaceTool(metadata=metadata, handler=failing_handler),),
        strict_approved_names=False,
    )

    with pytest.raises(WorkspaceToolExecutionError):
        await registry.execute(
            "test_tool",
            db=db_session,
            context=context,
            payload={"value": 7},
        )

    audit_entry = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == "workspace.test",
                AuditLog.resource_id == "test_tool",
            )
        )
    ).scalars().first()
    assert audit_entry is not None
    assert audit_entry.school_id == context.school_id
    assert audit_entry.user_id == context.teacher_user_id
    assert audit_entry.details["outcome"] == "execution_failed"
    assert audit_entry.details["attempt_count"] == 2
    assert audit_entry.details["error_type"] == "ConnectionError"
    assert audit_entry.details["correlation_id"] == "workspace-test-failure"


@pytest.mark.asyncio
async def test_teacher_navigation_targets_respect_existing_permissions(
    db_session,
    teacher_user,
    test_school,
    test_class,
    student_user,
):
    subject = Subject(
        school_id=test_school.id,
        class_id=test_class.id,
        name="Maths",
        code="MTH",
    )
    db_session.add(subject)
    await db_session.flush()
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=teacher_user.id,
            subject_id=subject.id,
            class_id=test_class.id,
            is_primary=True,
        )
    )
    await db_session.flush()

    student = (
        await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    ).scalar_one()

    registry = WorkspaceToolRegistry.load_default()
    result = await registry.execute(
        "get_teacher_navigation_targets",
        db=db_session,
        context=_context(teacher_user=teacher_user),
        payload={"student_id": str(student.id)},
    )
    actions = {action.href: action for action in result.actions}
    assert result.status == "ok"
    assert actions["/dashboard/teaching/exams"].enabled is True
    assert actions["/dashboard/teaching/gradebook"].enabled is True
    assert actions["/dashboard/teaching/report-cards"].enabled is False


@pytest.mark.asyncio
async def test_learning_evidence_report_denies_out_of_scope_subject(
    client,
    db_session,
    admin_user,
    teacher_user,
    student_user,
    test_school,
    test_class,
):
    weak, _subject, _flag, _evaluation = await _seed_grounded_flagging_report(
        client,
        db_session,
        admin_user=admin_user,
        teacher_user=admin_user,
        student_user=student_user,
        test_school=test_school,
        test_class=test_class,
    )
    science_teacher = teacher_user
    science = Subject(
        school_id=test_school.id,
        class_id=test_class.id,
        name="Science",
        code="SCI",
    )
    db_session.add(science)
    await db_session.flush()
    db_session.add(
        TeacherSubjectMapping(
            school_id=test_school.id,
            teacher_id=science_teacher.id,
            subject_id=science.id,
            class_id=test_class.id,
            is_primary=True,
        )
    )
    await db_session.flush()

    registry = WorkspaceToolRegistry.load_default()
    result = await registry.execute(
        "get_student_learning_evidence_report",
        db=db_session,
        context=_context(teacher_user=science_teacher),
        payload={"student_id": str(weak.id)},
    )
    assert result.status == "forbidden"
    assert result.student is not None
