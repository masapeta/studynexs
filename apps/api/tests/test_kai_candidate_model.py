"""EUI Phase 4 — KAI candidate model contracts."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.eui.schemas.knowledge_acquisition import (
    EducationalArtifactCandidate,
    KnowledgeAcquisitionInputReference,
    KnowledgeAcquisitionProvenance,
    KnowledgeAcquisitionTrustSignals,
)


def test_kai_feature_flag_defaults_off():
    assert Settings().EUI_KAI_PASSIVE_ENABLED is False


def test_kai_input_reference_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        KnowledgeAcquisitionInputReference.model_validate(
            {
                "tenant_id": str(uuid.uuid4()),
                "source_type": "pdf",
                "surprise": "not allowed",
            }
        )


def test_kai_trust_signal_confidence_is_bounded():
    with pytest.raises(ValidationError):
        KnowledgeAcquisitionTrustSignals(extraction_confidence=1.5)


def test_kai_candidate_is_never_authoritative_in_phase_4():
    tenant_id = uuid.uuid4()
    candidate = EducationalArtifactCandidate(
        id="kai://pdf/abc123",
        tenant_id=tenant_id,
        source_type="pdf",
        artifact_type="worksheet",
        modality="document",
        source_admission_status="admitted",
        extraction_status="supplied",
        review_status="candidate",
        provenance=KnowledgeAcquisitionProvenance(
            source="test",
        ),
        trust_signals=KnowledgeAcquisitionTrustSignals(review_required=True),
    )

    assert candidate.authoritative is False


def test_kai_candidate_rejects_non_kai_id():
    with pytest.raises(ValidationError):
        EducationalArtifactCandidate(
            id="artifact://not-kai",
            tenant_id=uuid.uuid4(),
            source_type="pdf",
            modality="document",
            source_admission_status="admitted",
            extraction_status="supplied",
            review_status="candidate",
            provenance=KnowledgeAcquisitionProvenance(source="test"),
            trust_signals=KnowledgeAcquisitionTrustSignals(),
        )
