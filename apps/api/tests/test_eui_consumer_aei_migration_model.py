"""EUI Phase 7A - AEI consumer migration model contracts."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.eui.schemas.aei_consumer_migration import (
    AEIConsumerMigrationCapture,
    AEIConsumerMigrationComparison,
    AEIConsumerMigrationDifference,
    AEIConsumerMigrationEvidenceBundle,
)


def test_phase_7a_feature_flags_default_off():
    settings = Settings()

    assert settings.EUI_CONSUMER_AEI_DUAL_READ_ENABLED is False
    assert settings.EUI_CONSUMER_AEI_RICH_EVIDENCE_ENABLED is False
    assert settings.EUI_CONSUMER_AEI_SOURCE_ENABLED is False


def test_comparison_is_strict_non_authoritative_and_serializable():
    tenant_id = uuid.uuid4()
    comparison = AEIConsumerMigrationComparison(
        id="eui-aei-migration://answer-sheet-evaluation/abc123",
        tenant_id=tenant_id,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        differences=(
            AEIConsumerMigrationDifference(
                difference_type="equivalent",
                reason="same_summary",
            ),
        ),
    )

    dumped = comparison.model_dump(mode="json")
    assert dumped["tenant_id"] == str(tenant_id)
    assert dumped["source_switch_active"] is False
    assert comparison.authoritative is False
    assert comparison.has_blockers is False
    assert comparison.difference_types == ("equivalent",)

    with pytest.raises(ValidationError):
        comparison.subject_ref = "changed"  # type: ignore[misc]

    with pytest.raises(ValidationError):
        AEIConsumerMigrationComparison(
            id="eui-aei-migration://answer-sheet-evaluation/abc123",
            tenant_id=tenant_id,
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:123",
            surprise=True,  # type: ignore[call-arg]
        )


def test_source_switch_active_cannot_be_true_in_phase_7a():
    with pytest.raises(ValidationError):
        AEIConsumerMigrationComparison(
            id="eui-aei-migration://answer-sheet-evaluation/abc123",
            tenant_id=uuid.uuid4(),
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:123",
            source_switch_active=True,
        )


def test_invalid_comparison_id_is_rejected():
    with pytest.raises(ValidationError):
        AEIConsumerMigrationComparison(
            id="migration://not-eui",
            tenant_id=uuid.uuid4(),
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:123",
        )


def test_capture_is_serializable_and_bounded_to_internal_status():
    capture = AEIConsumerMigrationCapture(
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        status="failed",
        duration_ms=0.1,
        error="synthetic failure",
    )

    assert capture.model_dump(mode="json")["status"] == "failed"

    with pytest.raises(ValidationError):
        AEIConsumerMigrationCapture(
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:123",
            status="teacher_visible",  # type: ignore[arg-type]
            duration_ms=0.1,
        )


def test_rich_evidence_bundle_is_strict_non_authoritative_and_serializable():
    tenant_id = uuid.uuid4()
    bundle = AEIConsumerMigrationEvidenceBundle(
        tenant_id=tenant_id,
        subject_type="answer_sheet_evaluation",
        subject_ref="answer_sheet_evaluation:123",
        status="partial",
        missing_evidence=("identity",),
        query_budget={"per_question_db_traversal": False},
    )

    dumped = bundle.model_dump(mode="json")
    assert dumped["tenant_id"] == str(tenant_id)
    assert bundle.authoritative is False
    assert bundle.query_budget["per_question_db_traversal"] is False

    with pytest.raises(ValidationError):
        AEIConsumerMigrationEvidenceBundle(
            tenant_id=tenant_id,
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:123",
            status="teacher_visible",  # type: ignore[arg-type]
        )

    with pytest.raises(ValidationError):
        AEIConsumerMigrationEvidenceBundle(
            tenant_id=tenant_id,
            subject_type="answer_sheet_evaluation",
            subject_ref="answer_sheet_evaluation:123",
            status="partial",
            raw_input="sensitive",  # type: ignore[call-arg]
        )
