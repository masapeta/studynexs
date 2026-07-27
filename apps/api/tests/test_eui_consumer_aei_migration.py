"""EUI Phase 7A - passive AEI consumer migration dual-read."""

from __future__ import annotations

import uuid

from app.core.platform_metrics import PlatformMetricsRegistry
from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextProvenance,
)
from app.modules.eui.schemas.trust_report import TrustDimension, TrustReport
from app.modules.eui.services import aei_consumer_migration as migration
from app.modules.eui.services.aei_consumer_migration import (
    AEIConsumerMigrationAdapter,
    classify_migration_differences,
    eui_aei_consumer_migration_captures,
    observe_aei_consumer_migration,
    stable_aei_consumer_migration_id,
)

TENANT_ID = uuid.UUID("11111111-1111-4111-8111-111111111111")


def setup_function() -> None:
    eui_aei_consumer_migration_captures.clear()


def teardown_function() -> None:
    eui_aei_consumer_migration_captures.clear()


def test_stable_migration_id_is_deterministic_and_avoids_subject_ref_text():
    first = stable_aei_consumer_migration_id(
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:secret-reference",
        payload={"status": "equivalent", "count": 1},
    )
    second = stable_aei_consumer_migration_id(
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:secret-reference",
        payload={"count": 1, "status": "equivalent"},
    )

    assert first == second
    assert first.startswith("eui-aei-migration://answer-sheet-evaluation/")
    assert "secret" not in first


def test_difference_classifier_covers_equivalent_eui_missing_and_eui_richer():
    equivalent = classify_migration_differences(
        legacy_summary={"available": True, "question_count": 2},
        eui_summary={"available": True, "question_count": 2},
    )
    assert _types(equivalent) == ("equivalent",)

    missing = classify_migration_differences(
        legacy_summary={"available": True},
        eui_summary={"available": False},
    )
    assert _types(missing) == ("eui_missing",)

    richer = classify_migration_differences(
        legacy_summary={"available": True},
        eui_summary={
            "available": True,
            "educational_identity_id": "ei://cbse/ncf2023/g6/science/ch05",
        },
    )
    assert _types(richer) == ("eui_richer",)


def test_difference_classifier_marks_product_impacting_and_unsafe_as_blockers():
    product = classify_migration_differences(
        legacy_summary={"result_hash": "legacy"},
        eui_summary={"available": True, "result_hash": "eui"},
    )
    assert _types(product) == ("product_impacting",)
    assert product[0].blocker is True

    unsafe = classify_migration_differences(
        legacy_summary={"tenant_id": "tenant-a"},
        eui_summary={"available": True, "tenant_id": "tenant-b"},
    )
    assert _types(unsafe) == ("unsafe",)
    assert unsafe[0].blocker is True


def test_difference_classifier_records_legacy_ambiguity_passively():
    differences = classify_migration_differences(
        legacy_summary={"available": True, "ambiguous": True},
        eui_summary={
            "available": True,
            "educational_identity_id": "ei://cbse/ncf2023/g8/physics/ch02",
        },
    )

    assert _types(differences) == ("legacy_ambiguous", "eui_richer")
    assert all(difference.blocker is False for difference in differences)


def test_trust_report_visibility_above_internal_is_unsafe():
    report = TrustReport(
        id="trust-report://educational-context/abc123",
        tenant_id=TENANT_ID,
        subject_type="educational_context",
        subject_ref="ei://cbse/ncf2023/g6/science/ch05",
        overall_posture="trusted",
        dimensions={
            "understanding_confidence": TrustDimension(
                status="strong",
                reason="context_resolved",
            )
        },
        review_required=False,
        evidence_available=True,
        consumer_visibility="teacher_safe",
    )

    differences = classify_migration_differences(
        legacy_summary={"available": True},
        eui_summary={"available": True},
        trust_report=report,
    )

    assert "unsafe" in _types(differences)
    assert any(difference.blocker for difference in differences)


def test_adapter_records_context_without_source_switch():
    comparison = AEIConsumerMigrationAdapter().build_comparison(
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        legacy_summary={"available": True},
        educational_context=_context(),
        source_flag_enabled=True,
    )

    assert comparison.eui_context_present is True
    assert comparison.eui_identity_present is True
    assert comparison.source_flag_enabled is True
    assert comparison.source_switch_active is False
    assert comparison.authoritative is False
    assert comparison.difference_types == ("eui_richer",)


def test_passive_observer_is_noop_when_disabled():
    capture = observe_aei_consumer_migration(
        enabled=False,
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        legacy_summary={"available": True},
        eui_summary={"available": True},
    )

    assert capture is None
    assert eui_aei_consumer_migration_captures.snapshot() == []


def test_passive_observer_captures_dual_read_when_enabled(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(migration, "platform_metrics", metrics)

    capture = observe_aei_consumer_migration(
        enabled=True,
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        legacy_summary={"available": True},
        eui_summary={"available": True},
    )

    assert capture is not None
    assert capture.status == "completed"
    assert capture.comparison is not None
    assert capture.comparison.authoritative is False
    assert eui_aei_consumer_migration_captures.snapshot()[-1] == capture
    snapshot = metrics.snapshot()
    assert snapshot["jobs_by_status"]["invoked"] == 1
    assert snapshot["jobs_by_status"]["completed"] == 1


def test_passive_observer_isolates_exceptions(monkeypatch):
    metrics = PlatformMetricsRegistry()
    monkeypatch.setattr(migration, "platform_metrics", metrics)

    class BrokenAdapter:
        def build_comparison(self, **_kwargs):  # noqa: ANN003, ANN201
            raise RuntimeError("synthetic migration failure")

    capture = observe_aei_consumer_migration(
        enabled=True,
        tenant_id=TENANT_ID,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        legacy_summary={"available": True},
        adapter=BrokenAdapter(),  # type: ignore[arg-type]
    )

    assert capture is None
    stored = eui_aei_consumer_migration_captures.snapshot()[-1]
    assert stored.status == "failed"
    assert stored.error == "synthetic migration failure"
    assert metrics.snapshot()["jobs_by_status"]["failed"] == 1


def _context() -> EducationalContext:
    return EducationalContext(
        tenant_id=TENANT_ID,
        resolution_status="resolved",
        grade="6",
        subject="Science",
        educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        field_sources={"grade": "educational_identity"},
        provenance=EducationalContextProvenance(
            source="context_resolver",
            resolved_from="educational_identity",
        ),
    )


def _types(differences) -> tuple[str, ...]:  # noqa: ANN001
    return tuple(difference.difference_type for difference in differences)
