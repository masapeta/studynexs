"""EUI Phase 7B — AEI rich EUI evidence binding foundation."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.platform_metrics import PlatformMetricsRegistry
from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationEvidenceBundle,
)
from app.modules.eui.services import aei_consumer_migration_evidence as rich_evidence
from app.modules.eui.services.aei_consumer_migration_evidence import (
    AEIConsumerMigrationEvidenceBinder,
    bind_aei_consumer_migration_evidence,
)
from app.modules.eui.services.educational_context_resolver import EducationalContextResolver
from app.modules.eui.services.trust_report_builder import TrustReportBuilder


def test_eui_aei_rich_evidence_bundle_is_internal_and_strict():
    tenant_id = uuid.uuid4()
    bundle = AEIConsumerMigrationEvidenceBundle(
        tenant_id=tenant_id,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:test",
        status="partial",
        missing_evidence=("identity",),
    )

    assert bundle.authoritative is False
    assert bundle.model_dump(mode="json")["tenant_id"] == str(tenant_id)

    with pytest.raises(ValidationError):
        AEIConsumerMigrationEvidenceBundle(
            tenant_id=tenant_id,
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:test",
            status="partial",
            student_answer="raw answer",
        )


@pytest.mark.asyncio
async def test_eui_aei_rich_evidence_disabled_is_noop(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(rich_evidence, "platform_metrics", metrics)

    def _unexpected_binder(*_args, **_kwargs):
        raise AssertionError("disabled rich evidence must not construct binder")

    monkeypatch.setattr(
        rich_evidence,
        "AEIConsumerMigrationEvidenceBinder",
        _unexpected_binder,
    )

    result = await bind_aei_consumer_migration_evidence(
        enabled=False,
        db=None,
        tenant_id=uuid.uuid4(),
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:test",
        question_paper=_paper(),
    )

    assert result is None
    assert metrics.snapshot()["job_events_total"] == 0


@pytest.mark.asyncio
async def test_eui_aei_rich_evidence_binds_context_capability_and_trust(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(rich_evidence, "platform_metrics", metrics)

    result = await bind_aei_consumer_migration_evidence(
        enabled=True,
        db=None,
        tenant_id=uuid.uuid4(),
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:test",
        artifact_id=uuid.uuid4(),
        exam=_exam(),
        question_paper=_paper(),
    )

    assert result is not None
    assert result.educational_context is not None
    assert result.capability_lookup is not None
    assert result.trust_report is not None
    assert result.trust_report.consumer_visibility == "internal_only"
    assert result.bundle.authoritative is False
    assert result.bundle.status == "partial"
    assert result.bundle.context_status == "resolved"
    assert result.bundle.capability_mode == "supported"
    assert result.bundle.capability_matched is True
    assert result.bundle.trust_report_ref is not None
    assert "identity" in result.bundle.missing_evidence
    assert result.bundle.query_budget["per_question_db_traversal"] is False
    assert result.eui_summary["runtime_authoritative"] is False

    snapshot = metrics.snapshot()
    assert snapshot["jobs_by_status"]["invoked"] == 1
    assert snapshot["jobs_by_status"]["partial"] == 1
    assert snapshot["jobs_by_status"]["missing_identity"] == 1


@pytest.mark.asyncio
async def test_eui_aei_rich_evidence_records_ambiguity_passively(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(rich_evidence, "platform_metrics", metrics)

    result = await bind_aei_consumer_migration_evidence(
        enabled=True,
        db=None,
        tenant_id=uuid.uuid4(),
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:ambiguous",
        artifact_id=uuid.uuid4(),
        exam=_exam(),
        question_paper=_paper(candidate_context_ids=("ctx-a", "ctx-b")),
    )

    assert result is not None
    assert result.bundle.status == "partial"
    assert result.bundle.ambiguous_evidence == ("context",)
    assert result.bundle.context_status == "ambiguous"
    assert metrics.snapshot()["jobs_by_status"]["ambiguous"] == 1


@pytest.mark.asyncio
async def test_eui_aei_rich_evidence_isolates_exceptions(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(rich_evidence, "platform_metrics", metrics)

    class BrokenResolver:
        async def resolve(self, _reference):  # noqa: ANN001
            raise RuntimeError("context resolver unavailable")

    binder = AEIConsumerMigrationEvidenceBinder(
        context_resolver=BrokenResolver(),  # type: ignore[arg-type]
    )
    result = await binder.bind(
        enabled=True,
        db=None,
        tenant_id=uuid.uuid4(),
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:failure",
        question_paper=_paper(),
    )

    assert result is not None
    assert result.bundle.status == "failed"
    assert result.bundle.authoritative is False
    assert metrics.snapshot()["jobs_by_status"]["failed"] == 1


@pytest.mark.asyncio
async def test_eui_aei_rich_evidence_marks_unsafe_trust_as_passive_evidence():
    tenant_id = uuid.uuid4()
    context = await async_resolve_context(tenant_id)
    report = TrustReportBuilder().build_for_context(context).model_copy(
        update={"consumer_visibility": "teacher_safe"}
    )
    bundle = rich_evidence._bundle(
        tenant_id=tenant_id,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:unsafe-trust",
        context=context,
        capability=None,
        trust=report,
        missing={"identity", "capability", "trust_unsafe"},
        ambiguous=set(),
        duration_ms=0.0,
    )

    assert bundle.trust_consumer_visibility == "teacher_safe"
    assert "trust_unsafe" in bundle.missing_evidence
    assert bundle.authoritative is False


async def async_resolve_context(tenant_id: uuid.UUID):
    result = await AEIConsumerMigrationEvidenceBinder(
        context_resolver=EducationalContextResolver()
    ).bind(
        enabled=True,
        db=None,
        tenant_id=tenant_id,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:trust-context",
        question_paper=_paper(),
    )
    assert result is not None
    assert result.educational_context is not None
    return result.educational_context


def _paper(*, candidate_context_ids: tuple[str, ...] = ()):
    return SimpleNamespace(
        pack_id=None,
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2026",
        grade="10",
        subject_name="Mathematics",
        topics=["Algebra"],
        language_medium="English",
        candidate_context_ids=candidate_context_ids,
    )


def _exam():
    return SimpleNamespace(
        exam_type=SimpleNamespace(value="unit_test"),
        topic=None,
        source_paper_id=None,
    )
