"""EUI Phase 6 - Trust Report model contracts."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.eui.schemas.trust_report import (
    TrustDimension,
    TrustProvenanceReference,
    TrustReport,
    TrustWarning,
)
from app.modules.eui.services.trust_report_id import stable_trust_report_id
from app.modules.eui.services.trust_report_policy import derive_overall_posture


def test_trust_report_feature_flag_defaults_off():
    assert Settings().EUI_TRUST_REPORT_ENABLED is False


def test_trust_dimension_is_strict_and_score_bounded():
    with pytest.raises(ValidationError):
        TrustDimension(status="strong", reason="test", score=1.25)

    with pytest.raises(ValidationError):
        TrustDimension(status="strong", reason="test", surprise=True)  # type: ignore[call-arg]


def test_trust_report_is_non_authoritative_and_serializable():
    tenant_id = uuid.uuid4()
    report = TrustReport(
        id="trust-report://kai-candidate/abc123",
        tenant_id=tenant_id,
        subject_type="kai_candidate",
        subject_ref="kai://pdf/abc123",
        overall_posture="manual_review_required",
        dimensions={
            "human_review_status": TrustDimension(
                status="weak",
                reason="candidate_requires_review",
                warnings=(
                    TrustWarning(
                        code="manual_review_required",
                        severity="blocker",
                        message="Human review is required before authoritative use.",
                    ),
                ),
            )
        },
        review_required=True,
        evidence_available=True,
        provenance_refs=(
            TrustProvenanceReference(source="kai", subject_ref="kai://pdf/abc123"),
        ),
    )

    dumped = report.model_dump(mode="json")
    assert dumped["tenant_id"] == str(tenant_id)
    assert dumped["provenance_refs"][0]["source"] == "kai"
    assert report.authoritative is False

    with pytest.raises(ValidationError):
        report.subject_ref = "changed"  # type: ignore[misc]


def test_trust_report_rejects_non_trust_report_id():
    with pytest.raises(ValidationError):
        TrustReport(
            id="report://not-trust",
            tenant_id=uuid.uuid4(),
            subject_type="educational_context",
            subject_ref="ctx",
            overall_posture="trusted",
            dimensions={
                "understanding_confidence": TrustDimension(
                    status="strong",
                    reason="test",
                )
            },
            review_required=False,
            evidence_available=True,
        )


def test_stable_trust_report_id_is_deterministic_and_avoids_raw_subject_text():
    report_id = stable_trust_report_id(
        subject_type="kai_candidate",
        subject_ref="secret worksheet label",
        payload={"overall_posture": "trusted", "score": 0.99},
    )

    assert report_id.startswith("trust-report://kai-candidate/")
    assert "secret" not in report_id
    assert report_id == stable_trust_report_id(
        subject_type="kai_candidate",
        subject_ref="secret worksheet label",
        payload={"score": 0.99, "overall_posture": "trusted"},
    )


def test_posture_precedence_is_conservative_not_score_averaged():
    dimensions = {
        "input_quality": TrustDimension(status="strong", score=1.0, reason="clear_input"),
        "ocr_confidence": TrustDimension(status="strong", score=0.98, reason="ocr_high"),
        "capability_mode": TrustDimension(
            status="unsupported",
            score=1.0,
            reason="capability_unsupported",
        ),
    }

    assert derive_overall_posture(dimensions) == "unsupported"


def test_blocker_warning_requires_manual_review():
    dimensions = {
        "evidence_availability": TrustDimension(status="strong", reason="evidence_present"),
        "human_review_status": TrustDimension(
            status="weak",
            reason="review_required",
            warnings=(
                TrustWarning(
                    code="manual_review_required",
                    severity="blocker",
                    message="Human review is required.",
                ),
            ),
        ),
    }

    assert derive_overall_posture(dimensions) == "manual_review_required"
