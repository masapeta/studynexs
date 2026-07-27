"""EUI Phase 5 - Educational Graph proposal model contracts."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.modules.eui.schemas.educational_graph import (
    EducationalGraphProvenance,
    EducationalGraphReference,
    EducationalGraphRelationshipProposal,
    EducationalGraphRelationshipReference,
    EducationalGraphTrustPlaceholders,
)


def test_ekg_expansion_feature_flag_defaults_off():
    assert Settings().EUI_EKG_EXPANSION_ENABLED is False


def test_graph_relationship_reference_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        EducationalGraphRelationshipReference.model_validate(
            {
                "tenant_id": str(uuid.uuid4()),
                "educational_identity_id": "ei://cbse/ncf2023/g6/science/ch05",
                "surprise": "not allowed",
            }
        )


def test_graph_proposal_rejects_non_proposal_id():
    with pytest.raises(ValidationError):
        EducationalGraphRelationshipProposal(
            id="kg://not-a-proposal",
            tenant_id=uuid.uuid4(),
            relationship_category="identity_link",
            status="proposed",
            from_reference=EducationalGraphReference(
                reference_type="educational_identity",
                id="ei://cbse/ncf2023/g6/science/ch05",
            ),
            to_reference=EducationalGraphReference(
                reference_type="kg_node",
                id=str(uuid.uuid4()),
                node_type="concept",
            ),
            authority_posture="candidate",
            provenance=EducationalGraphProvenance(
                source="test",
                relationship_source="test",
            ),
            trust_placeholders=EducationalGraphTrustPlaceholders(),
        )


def test_graph_proposal_is_never_authoritative_in_phase_5():
    proposal = EducationalGraphRelationshipProposal(
        id="ekg-proposal://identity-link/abc123",
        tenant_id=uuid.uuid4(),
        relationship_category="identity_link",
        status="proposed",
        from_reference=EducationalGraphReference(
            reference_type="educational_identity",
            id="ei://cbse/ncf2023/g6/science/ch05",
        ),
        to_reference=EducationalGraphReference(
            reference_type="kg_node",
            id=str(uuid.uuid4()),
            node_type="concept",
        ),
        authority_posture="candidate",
        provenance=EducationalGraphProvenance(
            source="test",
            relationship_source="test",
        ),
        trust_placeholders=EducationalGraphTrustPlaceholders(review_required=True),
    )

    assert proposal.authoritative is False
