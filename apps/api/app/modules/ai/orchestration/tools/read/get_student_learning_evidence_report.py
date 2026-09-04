"""Build the deterministic Phase 0 student learning-evidence report."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import Field
from sqlalchemy import or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import assert_can_access_student
from app.core.staff_permissions import get_staff_scope
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.mastery import MasteryFlag
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext, WorkspaceToolMetadata
from app.modules.ai.orchestration.tools.read._shared import (
    current_user_from_context,
    load_student_card_payload,
)
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)
from app.modules.mastery.schemas.mastery import LearningEvidenceChainOut
from app.modules.mastery.services.learning_evidence_service import build_learning_evidence_chain
from app.modules.workspace.schemas.blocks import (
    MetricRowPayload,
    StudentCardPayload,
    TablePayload,
    WorkspaceCitation,
    WorkspaceMetricItem,
    WorkspaceSchemaModel,
    WorkspaceTableColumn,
)


class GetStudentLearningEvidenceReportInput(WorkspaceSchemaModel):
    student_id: uuid.UUID


class GetStudentLearningEvidenceReportOutput(WorkspaceSchemaModel):
    status: Literal["ok", "forbidden", "not_found"]
    student: StudentCardPayload | None = None
    summary_metrics: MetricRowPayload | None = None
    weak_concepts: TablePayload | None = None
    recent_assessment_evidence: TablePayload | None = None
    citations: list[WorkspaceCitation] = Field(default_factory=list)
    verification_status: Literal[
        "verified", "stale", "missing", "conflicting", "requires_approval"
    ] = "missing"
    checked_at: datetime | None = None
    detail: str | None = None


def _metric_status(value: float | int | None, *, warn_below: float, risk_below: float) -> str:
    if value is None:
        return "warning"
    numeric = float(value)
    if numeric < risk_below:
        return "risk"
    if numeric < warn_below:
        return "warning"
    return "normal"


def _build_summary_metrics(chain: LearningEvidenceChainOut) -> MetricRowPayload:
    mastery_pct = chain.mastery.mastery_pct if chain.mastery is not None else None
    return MetricRowPayload(
        items=[
            WorkspaceMetricItem(
                label="Mastery",
                value="—" if mastery_pct is None else f"{mastery_pct:.1f}%",
                status=_metric_status(mastery_pct, warn_below=70.0, risk_below=40.0),
            ),
            WorkspaceMetricItem(
                label="Weak concepts",
                value=chain.weak_concept_count,
                status="warning" if chain.weak_concept_count else "normal",
            ),
            WorkspaceMetricItem(
                label="Recent assessments",
                value=len(chain.exams),
                status="warning" if not chain.exams else "normal",
            ),
            WorkspaceMetricItem(
                label="Approved evaluations",
                value=len(chain.approved_evaluation_ids),
                status="warning" if not chain.approved_evaluation_ids else "normal",
            ),
        ]
    )


def _build_weak_concepts_table(
    rows: list[tuple[CurriculumConcept, dict | None]],
) -> TablePayload:
    return TablePayload(
        columns=[
            WorkspaceTableColumn(key="concept", label="Weak concept"),
            WorkspaceTableColumn(key="topic", label="Topic"),
            WorkspaceTableColumn(key="mastery_pct", label="Mastery %"),
        ],
        rows=[
            {
                "concept": concept.title,
                "topic": (meta or {}).get("topic") or "—",
                "mastery_pct": (
                    round(float((meta or {}).get("mastery_pct")), 1)
                    if (meta or {}).get("mastery_pct") is not None
                    else None
                ),
            }
            for concept, meta in rows
        ],
        empty_message="No weak-concept links are available for this student yet.",
    )


def _build_assessment_table(chain: LearningEvidenceChainOut) -> TablePayload:
    exams = sorted(
        chain.exams,
        key=lambda exam: (exam.assessed_on is None, exam.assessed_on),
        reverse=True,
    )
    return TablePayload(
        columns=[
            WorkspaceTableColumn(key="assessment", label="Assessment"),
            WorkspaceTableColumn(key="date", label="Date"),
            WorkspaceTableColumn(key="topic_pct", label="Topic %"),
            WorkspaceTableColumn(key="marks", label="Marks"),
            WorkspaceTableColumn(key="grounded", label="Grounded"),
        ],
        rows=[
            {
                "assessment": exam.title,
                "date": exam.assessed_on.isoformat() if exam.assessed_on else "—",
                "topic_pct": round(exam.topic_pct, 1) if exam.topic_pct is not None else None,
                "marks": (
                    f"{exam.marks_obtained:.1f}/{exam.total_marks:.1f}"
                    if exam.marks_obtained is not None and exam.total_marks is not None
                    else "—"
                ),
                "grounded": exam.question_paper_grounded,
            }
            for exam in exams
        ],
        empty_message="No recent assessment evidence is available for this student.",
    )


def _build_citations(chain: LearningEvidenceChainOut) -> list[WorkspaceCitation]:
    citations: list[WorkspaceCitation] = []
    seen: set[tuple[str, str]] = set()
    for exam in chain.exams:
        if exam.curriculum_pack_id:
            key = ("curriculum_pack", str(exam.curriculum_pack_id))
            if key not in seen:
                seen.add(key)
                citations.append(
                    WorkspaceCitation(
                        label="Curriculum pack link",
                        source_type="curriculum_pack",
                        source_id=str(exam.curriculum_pack_id),
                        summary=f"{exam.title} is linked to an approved curriculum pack.",
                    )
                )
        if exam.question_paper_id:
            key = ("question_paper", str(exam.question_paper_id))
            if key not in seen:
                seen.add(key)
                citations.append(
                    WorkspaceCitation(
                        label="Question paper link",
                        source_type="question_paper",
                        source_id=str(exam.question_paper_id),
                        summary=f"{exam.title} is backed by a grounded question paper.",
                    )
                )
        for evaluation_id in exam.approved_evaluation_ids:
            key = ("answer_sheet_evaluation", str(evaluation_id))
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                WorkspaceCitation(
                    label="Approved evaluation",
                    source_type="answer_sheet_evaluation",
                    source_id=str(evaluation_id),
                    summary=f"{exam.title} includes an approved answer-sheet evaluation.",
                )
            )
    return citations


def _verification_status(chain: LearningEvidenceChainOut) -> str:
    if chain.grounded and not chain.warnings:
        return "verified"
    if chain.exams or chain.curriculum_pack_ids or chain.question_paper_ids:
        return "conflicting"
    return "missing"


async def _load_latest_accessible_flag(
    db: AsyncSession,
    *,
    context: WorkspaceToolContext,
    student_id: uuid.UUID,
) -> MasteryFlag | None:
    current_user = current_user_from_context(context)
    scope = await get_staff_scope(db, current_user)
    filters = [
        MasteryFlag.school_id == context.school_id,
        MasteryFlag.student_id == student_id,
    ]
    if not scope.is_admin:
        clauses = []
        if scope.incharge_class_ids:
            clauses.append(MasteryFlag.class_id.in_(scope.incharge_class_ids))
        if scope.teaching_pairs:
            clauses.append(
                tuple_(MasteryFlag.class_id, MasteryFlag.subject_id).in_(
                    scope.teaching_pairs
                )
            )
        if not clauses:
            return None
        filters.append(or_(*clauses))

    return (
        await db.execute(
            select(MasteryFlag)
            .where(*filters)
            .order_by(MasteryFlag.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def get_student_learning_evidence_report(
    db: AsyncSession,
    context: WorkspaceToolContext,
    payload: GetStudentLearningEvidenceReportInput,
) -> GetStudentLearningEvidenceReportOutput:
    current_user = current_user_from_context(context)
    await assert_can_access_student(current_user, db, payload.student_id)
    student = await load_student_card_payload(
        db,
        school_id=context.school_id,
        student_id=payload.student_id,
    )
    if student is None:
        return GetStudentLearningEvidenceReportOutput(
            status="not_found",
            detail="Student not found in this school.",
        )

    flag = await _load_latest_accessible_flag(
        db,
        context=context,
        student_id=payload.student_id,
    )
    if flag is None:
        any_flag = (
            await db.execute(
                select(MasteryFlag.id)
                .where(
                    MasteryFlag.school_id == context.school_id,
                    MasteryFlag.student_id == payload.student_id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        status = "forbidden" if any_flag is not None else "not_found"
        detail = (
            "No mastery evidence for this student is available in your teaching scope."
            if status == "forbidden"
            else "No mastery evidence report is available for this student yet."
        )
        return GetStudentLearningEvidenceReportOutput(
            status=status,
            student=student,
            detail=detail,
        )

    chain = await build_learning_evidence_chain(
        db,
        school_id=context.school_id,
        tenant_slug=context.tenant_slug,
        flag=flag,
    )
    weak_concepts = await StudentWeakConceptService(db).get_weak_concepts_for_student(
        school_id=context.school_id,
        student_id=payload.student_id,
        subject_id=flag.subject_id,
    )

    return GetStudentLearningEvidenceReportOutput(
        status="ok",
        student=student,
        summary_metrics=_build_summary_metrics(chain),
        weak_concepts=_build_weak_concepts_table(weak_concepts[:5]),
        recent_assessment_evidence=_build_assessment_table(chain),
        citations=_build_citations(chain),
        verification_status=_verification_status(chain),
        checked_at=datetime.now(timezone.utc),
        detail=None,
    )


TOOL_METADATA = WorkspaceToolMetadata(
    name="get_student_learning_evidence_report",
    input_schema=GetStudentLearningEvidenceReportInput,
    output_schema=GetStudentLearningEvidenceReportOutput,
    allowed_roles=["teacher", "class_incharge"],
    scope_rule=(
        "student access plus mastery-flag subject scope using existing deterministic "
        "services"
    ),
    audit_event_type="workspace.read.get_student_learning_evidence_report",
    pii_level="medium",
    max_payload_size=256,
    tool_result_cache_policy="per_turn",
    timeout_ms=1200,
    retry_count=1,
    circuit_breaker_threshold=3,
    circuit_breaker_cooldown_seconds=60,
)
TOOL_HANDLER = get_student_learning_evidence_report
