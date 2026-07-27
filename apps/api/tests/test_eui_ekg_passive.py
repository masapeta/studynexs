"""EUI Phase 5 - passive EKG proposal observer."""

from __future__ import annotations

import uuid

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.educational_graph import EducationalGraphRelationshipReference
from app.modules.eui.schemas.educational_identity import (
    EducationalIdentity,
    EducationalIdentityProvenance,
)
from app.modules.eui.services.educational_graph_passive import (
    EUI_EKG_METRIC_TASK,
    educational_graph_passive_captures,
    observe_educational_graph_proposal,
)


def test_ekg_passive_observer_is_noop_when_disabled():
    educational_graph_passive_captures.clear()

    capture = observe_educational_graph_proposal(
        enabled=False,
        reference=EducationalGraphRelationshipReference(
            tenant_id=_tenant_id(),
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        ),
    )

    assert capture is None
    assert educational_graph_passive_captures.snapshot() == []


def test_ekg_passive_observer_captures_identity_link_success():
    educational_graph_passive_captures.clear()

    capture = observe_educational_graph_proposal(
        enabled=True,
        reference=EducationalGraphRelationshipReference(
            tenant_id=_tenant_id(),
            educational_identity=_identity(concept_id=uuid.uuid4()),
        ),
    )

    assert capture is not None
    assert capture.status == "identity_link_found"
    assert capture.proposal is not None
    assert capture.proposal.authoritative is False
    assert educational_graph_passive_captures.snapshot()[-1] == capture
    assert f'task="{EUI_EKG_METRIC_TASK}",status="identity_link_found"' in (
        platform_metrics.prometheus_text()
    )


def test_ekg_passive_observer_records_missing_identity_link():
    educational_graph_passive_captures.clear()

    capture = observe_educational_graph_proposal(
        enabled=True,
        reference=EducationalGraphRelationshipReference(
            tenant_id=_tenant_id(),
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        ),
    )

    assert capture is not None
    assert capture.status == "identity_link_missing"
    assert capture.proposal is not None
    assert capture.proposal.status == "missing_target"


def test_ekg_passive_observer_isolates_exceptions():
    class BrokenResolver:
        def propose(self, _reference):
            raise RuntimeError("synthetic EKG failure")

    capture = observe_educational_graph_proposal(
        enabled=True,
        reference=EducationalGraphRelationshipReference(
            tenant_id=_tenant_id(),
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        ),
        resolver=BrokenResolver(),  # type: ignore[arg-type]
    )

    assert capture is None
    assert f'task="{EUI_EKG_METRIC_TASK}",status="resolve_failed"' in (
        platform_metrics.prometheus_text()
    )


def _identity(*, concept_id: uuid.UUID) -> EducationalIdentity:
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
        metadata={"concept_id": str(concept_id)},
        provenance=EducationalIdentityProvenance(
            source="test",
            source_id=str(concept_id),
            source_version="2024",
            resolved_from="concept",
        ),
    )


def _tenant_id() -> uuid.UUID:
    return uuid.UUID("11111111-1111-4111-8111-111111111111")
