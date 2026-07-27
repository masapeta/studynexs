"""EUI Phase 5 - Educational Graph proposal resolver."""

from __future__ import annotations

import uuid

from app.modules.eui.schemas.educational_graph import (
    EducationalGraphReference,
    EducationalGraphRelationshipReference,
)
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)
from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference
from app.modules.eui.services.educational_graph_proposal_id import (
    stable_educational_graph_proposal_id,
)
from app.modules.eui.services.educational_graph_resolver import (
    EducationalGraphProposalResolver,
)
from app.modules.eui.services.knowledge_acquisition_builder import (
    KnowledgeAcquisitionCandidateBuilder,
)


def test_resolver_maps_identity_metadata_to_existing_kg_concept_proposal():
    concept_id = uuid.uuid4()
    reference = EducationalGraphRelationshipReference(
        tenant_id=_tenant_id(),
        educational_identity=_identity(concept_id=concept_id),
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.id == stable_educational_graph_proposal_id(
        reference,
        relationship_category="identity_link",
        status="proposed",
        target_reference_id=str(concept_id),
    )
    assert proposal.relationship_category == "identity_link"
    assert proposal.status == "proposed"
    assert proposal.to_reference.reference_type == "kg_node"
    assert proposal.to_reference.node_type == "concept"
    assert proposal.to_reference.id == str(concept_id)
    assert proposal.authority_posture == "candidate"
    assert proposal.authoritative is False
    assert proposal.provenance.metadata["proposal_only"] is True


def test_resolver_marks_identity_without_graph_target_missing():
    reference = EducationalGraphRelationshipReference(
        tenant_id=_tenant_id(),
        educational_identity=_identity(concept_id=None),
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.status == "missing_target"
    assert proposal.authority_posture == "needs_review"
    assert proposal.to_reference.reference_type == "unknown"
    assert proposal.trust_placeholders.ambiguity_count == 1
    assert proposal.ambiguities[0].reason == "identity_has_no_graph_target"


def test_resolver_marks_multiple_graph_targets_ambiguous():
    target_a = EducationalGraphReference(
        reference_type="kg_node",
        id=str(uuid.uuid4()),
        node_type="concept",
        label="Standard Units",
    )
    target_b = EducationalGraphReference(
        reference_type="kg_node",
        id=str(uuid.uuid4()),
        node_type="concept",
        label="SI Units",
    )
    reference = EducationalGraphRelationshipReference(
        tenant_id=_tenant_id(),
        educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        candidate_target_references=(target_a, target_b),
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.status == "ambiguous"
    assert proposal.authority_posture == "ambiguous"
    assert proposal.ambiguities[0].reason == "multiple_graph_targets"
    assert len(proposal.ambiguities[0].candidates) == 2


def test_resolver_builds_candidate_evidence_proposal_without_authority():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        KnowledgeAcquisitionInputReference(
            tenant_id=_tenant_id(),
            source_type="pdf",
            artifact_type="worksheet",
            supplied_extracted_text="Measure the classroom table.",
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
            educational_context_summary={
                "board": "CBSE",
                "grade": "6",
                "subject": "Science",
            },
        )
    )
    reference = EducationalGraphRelationshipReference(
        tenant_id=candidate.tenant_id,
        kai_candidate=candidate,
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.relationship_category == "candidate_evidence"
    assert proposal.status == "proposed"
    assert proposal.source_candidate_id == candidate.id
    assert proposal.to_reference.reference_type == "educational_identity"
    assert proposal.to_reference.id == "ei://cbse/ncf2023/g6/science/ch05"
    assert proposal.authority_posture == "candidate"
    assert proposal.trust_placeholders.review_required is True
    assert proposal.authoritative is False
    assert "Measure" not in proposal.id


def test_resolver_keeps_unsupported_kai_candidate_out_of_graph_authority():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        KnowledgeAcquisitionInputReference(
            tenant_id=_tenant_id(),
            source_type="image",
            artifact_type="diagram",
            supplied_extracted_text="untrusted image content",
        )
    )
    reference = EducationalGraphRelationshipReference(
        tenant_id=candidate.tenant_id,
        kai_candidate=candidate,
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.status == "unsupported"
    assert proposal.authority_posture == "unsupported"
    assert proposal.authoritative is False


def test_resolver_rejects_cross_tenant_candidate_as_unsupported():
    candidate = KnowledgeAcquisitionCandidateBuilder().build(
        KnowledgeAcquisitionInputReference(
            tenant_id=_tenant_id(),
            source_type="pdf",
            artifact_type="worksheet",
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
            educational_context_summary={"board": "CBSE"},
        )
    )
    reference = EducationalGraphRelationshipReference(
        tenant_id=uuid.UUID("22222222-2222-4222-8222-222222222222"),
        kai_candidate=candidate,
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.status == "unsupported"
    assert proposal.ambiguities[0].reason == "tenant_mismatch"


def test_resolver_rejects_cross_tenant_identity_as_unsupported():
    reference = EducationalGraphRelationshipReference(
        tenant_id=uuid.UUID("22222222-2222-4222-8222-222222222222"),
        educational_identity=_identity(concept_id=uuid.uuid4()),
    )

    proposal = EducationalGraphProposalResolver().propose(reference)

    assert proposal.status == "unsupported"
    assert proposal.authority_posture == "unsupported"
    assert proposal.ambiguities[0].reason == "identity_tenant_mismatch"


def _identity(*, concept_id: uuid.UUID | None) -> EducationalIdentity:
    metadata = {"concept_id": str(concept_id)} if concept_id else {}
    return EducationalIdentity(
        id="ei://cbse/ncf2023/g6/science/ch05/concept08",
        tenant_id=_tenant_id(),
        board="CBSE",
        curriculum="NCF2023",
        curriculum_version="2024",
        grade="6",
        subject="Science",
        chapter="Motion and Measurement of Distances",
        topic="Standard Units",
        concepts=("SI Units",),
        metadata=metadata,
        provenance=EducationalIdentityProvenance(
            source="test",
            source_id=str(concept_id) if concept_id else None,
            source_version="2024",
            resolved_from="concept",
        ),
    )


def _tenant_id() -> uuid.UUID:
    return uuid.UUID("11111111-1111-4111-8111-111111111111")
