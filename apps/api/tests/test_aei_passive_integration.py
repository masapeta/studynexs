import uuid

import pytest

from app.core.platform_metrics import PlatformMetricsRegistry
from app.db.models.answer_sheet_evaluation import (
    EVAL_STATUS_PROCESSING,
    AnswerSheetEvaluation,
)
from app.modules.eui.services.aei_consumer_migration import (
    eui_aei_consumer_migration_captures,
)
from app.modules.examinations.services import aei_passive_integration as passive
from app.modules.examinations.services import answer_sheet_eval_service as eval_mod
from app.modules.examinations.services.aei_passive_integration import (
    aei_passive_capture_registry,
    observe_answer_sheet_evaluation,
)
from app.modules.examinations.services.answer_sheet_eval_service import AnswerSheetEvalService
from tests.test_answer_sheet_eval import _seed_eval_fixture


@pytest.fixture(autouse=True)
def _clear_passive_captures():
    aei_passive_capture_registry.clear()
    eui_aei_consumer_migration_captures.clear()
    yield
    aei_passive_capture_registry.clear()
    eui_aei_consumer_migration_captures.clear()


def _student_answers() -> dict[str, str]:
    return {
        "1": "4",
        "2": "B",
        "3": "plants use sunlight to make food",
    }


def _suggestions() -> dict[str, dict]:
    return {
        "1": {"confidence": 0.98, "method": "objective"},
        "2": {"confidence": 0.98, "method": "objective"},
        "3": {"confidence": 0.55, "method": "heuristic_fallback"},
    }


@pytest.mark.asyncio
async def test_aei_passive_observer_disabled_does_not_capture(db_session):
    fx = await _seed_eval_fixture(db_session)

    result = await observe_answer_sheet_evaluation(
        enabled=False,
        db=db_session,
        evaluation_id=uuid.uuid4(),
        school_id=fx["school"].id,
        exam=fx["exam"],
        student_id=fx["student"].id,
        student_answers=_student_answers(),
        suggestions=_suggestions(),
    )

    assert result is None
    assert aei_passive_capture_registry.snapshot() == []


@pytest.mark.asyncio
async def test_aei_passive_observer_captures_complete_pipeline_when_enabled(
    db_session,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(passive, "platform_metrics", metrics)

    capture = await observe_answer_sheet_evaluation(
        enabled=True,
        db=db_session,
        evaluation_id=uuid.uuid4(),
        school_id=fx["school"].id,
        exam=fx["exam"],
        student_id=fx["student"].id,
        student_answers=_student_answers(),
        suggestions=_suggestions(),
    )

    assert capture is not None
    assert capture.question_count == 3
    assert len(aei_passive_capture_registry.snapshot()) == 1
    first = capture.questions[0]
    assert first.academic_answer["raw_input"] == "4"
    assert "reasoning_type" in first.academic_reasoning_result
    assert "decision" in first.policy_decision
    assert first.teacher_review_decision["review_status"] == "PENDING"
    assert first.teacher_review_decision["policy_decision"] == first.policy_decision
    assert capture.shadow_comparison is None
    snapshot = metrics.snapshot()
    assert snapshot["jobs_by_status"]["invoked"] == 1
    assert snapshot["jobs_by_status"]["completed"] == 1


@pytest.mark.asyncio
async def test_aei_shadow_mode_adds_internal_comparison_when_enabled(
    db_session,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(passive, "platform_metrics", metrics)

    capture = await observe_answer_sheet_evaluation(
        enabled=True,
        shadow_enabled=True,
        db=db_session,
        evaluation_id=uuid.uuid4(),
        school_id=fx["school"].id,
        exam=fx["exam"],
        student_id=fx["student"].id,
        student_answers=_student_answers(),
        suggestions=_suggestions(),
    )

    assert capture is not None
    assert capture.shadow_comparison is not None
    assert capture.shadow_comparison.question_count == 3
    assert len(capture.shadow_comparison.comparisons) == 3
    first = capture.shadow_comparison.comparisons[0]
    assert first.question_no == "1"
    assert first.production_method == "objective"
    assert first.aei_decision in {"supported", "manual_review", "unsupported"}
    snapshot = metrics.snapshot()
    assert snapshot["jobs_by_status"]["invoked"] == 2
    assert snapshot["jobs_by_status"]["completed"] == 2


def test_aei_shadow_comparison_classifies_manual_review_delta():
    comparison = passive._compare_shadow_question(
        question_no="7",
        suggestion={
            "method": "objective",
            "confidence": 0.98,
            "marks_suggested": 2,
            "max_marks": 2,
        },
        policy_decision={
            "decision": "manual_review",
            "manual_review_required": True,
            "supported_capability": True,
            "reason": "Capability is checklist-only.",
            "capability_mode": "checklist",
        },
    )

    assert comparison.comparison_status == "difference"
    assert "manual_review_signal_delta" in comparison.difference_categories
    assert comparison.production_review_signal is False
    assert comparison.aei_manual_review_required is True


@pytest.mark.asyncio
async def test_aei_passive_observer_isolates_exceptions(db_session, monkeypatch):
    fx = await _seed_eval_fixture(db_session)
    metrics = PlatformMetricsRegistry()

    class BrokenUnderstandingEngine:
        def understand(self, answer):  # pragma: no cover - exercised through observer
            raise RuntimeError("passive AEI failure")

    monkeypatch.setattr(passive, "AcademicUnderstandingEngine", BrokenUnderstandingEngine)
    monkeypatch.setattr(passive, "platform_metrics", metrics)

    result = await observe_answer_sheet_evaluation(
        enabled=True,
        db=db_session,
        evaluation_id=uuid.uuid4(),
        school_id=fx["school"].id,
        exam=fx["exam"],
        student_id=fx["student"].id,
        student_answers=_student_answers(),
        suggestions=_suggestions(),
    )

    assert result is None
    assert aei_passive_capture_registry.snapshot() == []
    snapshot = metrics.snapshot()
    assert snapshot["jobs_by_status"]["invoked"] == 1
    assert snapshot["jobs_by_status"]["failed"] == 1


@pytest.mark.asyncio
async def test_eval_outputs_identical_with_aei_passive_and_shadow_enabled(
    db_session,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)

    async def _llm_unavailable(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("app.modules.ai.services.evaluation_engine.generate_llm", _llm_unavailable)
    service = AnswerSheetEvalService(db_session)
    row = AnswerSheetEvaluation(
        school_id=fx["school"].id,
        exam_id=fx["exam"].id,
        student_id=fx["student"].id,
        input_answers=_student_answers(),
        created_by=fx["incharge"].id,
        status=EVAL_STATUS_PROCESSING,
    )
    db_session.add(row)
    await db_session.flush()

    monkeypatch.setattr(eval_mod.settings, "AEI_PASSIVE_INTEGRATION_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "AEI_SHADOW_MODE_ENABLED", False)
    disabled = await service.execute_evaluation(row.id, role="class_incharge")
    disabled_snapshot = {
        "status": disabled.status,
        "ai_suggestions": disabled.ai_suggestions,
        "correction_summary": disabled.correction_summary,
        "error_message": disabled.error_message,
    }

    row.status = EVAL_STATUS_PROCESSING
    row.ai_suggestions = None
    row.correction_summary = None
    row.error_message = None
    await db_session.flush()

    monkeypatch.setattr(eval_mod.settings, "AEI_PASSIVE_INTEGRATION_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "AEI_SHADOW_MODE_ENABLED", True)
    enabled = await service.execute_evaluation(row.id, role="class_incharge")
    enabled_snapshot = {
        "status": enabled.status,
        "ai_suggestions": enabled.ai_suggestions,
        "correction_summary": enabled.correction_summary,
        "error_message": enabled.error_message,
    }

    assert enabled_snapshot == disabled_snapshot
    assert len(aei_passive_capture_registry.snapshot()) == 1
    assert aei_passive_capture_registry.snapshot()[0].shadow_comparison is not None


@pytest.mark.asyncio
async def test_eval_outputs_identical_with_eui_aei_dual_read_and_source_flag_enabled(
    db_session,
    monkeypatch,
):
    fx = await _seed_eval_fixture(db_session)

    async def _llm_unavailable(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr("app.modules.ai.services.evaluation_engine.generate_llm", _llm_unavailable)
    service = AnswerSheetEvalService(db_session)
    row = AnswerSheetEvaluation(
        school_id=fx["school"].id,
        exam_id=fx["exam"].id,
        student_id=fx["student"].id,
        input_answers=_student_answers(),
        created_by=fx["incharge"].id,
        status=EVAL_STATUS_PROCESSING,
    )
    db_session.add(row)
    await db_session.flush()

    monkeypatch.setattr(eval_mod.settings, "AEI_PASSIVE_INTEGRATION_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "AEI_SHADOW_MODE_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "EUI_CONSUMER_AEI_DUAL_READ_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "EUI_CONSUMER_AEI_SOURCE_ENABLED", False)
    disabled = await service.execute_evaluation(row.id, role="class_incharge")
    disabled_snapshot = {
        "status": disabled.status,
        "ai_suggestions": disabled.ai_suggestions,
        "correction_summary": disabled.correction_summary,
        "error_message": disabled.error_message,
    }

    row.status = EVAL_STATUS_PROCESSING
    row.ai_suggestions = None
    row.correction_summary = None
    row.error_message = None
    await db_session.flush()

    monkeypatch.setattr(eval_mod.settings, "AEI_PASSIVE_INTEGRATION_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "AEI_SHADOW_MODE_ENABLED", False)
    monkeypatch.setattr(eval_mod.settings, "EUI_CONSUMER_AEI_DUAL_READ_ENABLED", True)
    monkeypatch.setattr(eval_mod.settings, "EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED", True)
    monkeypatch.setattr(eval_mod.settings, "EUI_CONSUMER_AEI_SOURCE_ENABLED", True)
    enabled = await service.execute_evaluation(row.id, role="class_incharge")
    enabled_snapshot = {
        "status": enabled.status,
        "ai_suggestions": enabled.ai_suggestions,
        "correction_summary": enabled.correction_summary,
        "error_message": enabled.error_message,
    }

    assert enabled_snapshot == disabled_snapshot
    assert len(aei_passive_capture_registry.snapshot()) == 1
    assert len(eui_aei_consumer_migration_captures.snapshot()) == 1
    comparison = eui_aei_consumer_migration_captures.snapshot()[0].comparison
    assert comparison is not None
    assert comparison.source_flag_enabled is True
    assert comparison.source_switch_active is False
    assert comparison.authoritative is False
    assert comparison.eui_context_present is True
    assert comparison.trust_report_ref is not None
    assert comparison.trust_consumer_visibility == "internal_only"
    assert comparison.eui_summary["rich_evidence_status"] in {"partial", "resolved"}
