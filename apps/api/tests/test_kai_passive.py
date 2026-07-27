"""EUI Phase 4 — passive KAI observer."""

from __future__ import annotations

import uuid

from app.core.platform_metrics import platform_metrics
from app.modules.eui.schemas.knowledge_acquisition import KnowledgeAcquisitionInputReference
from app.modules.eui.services.knowledge_acquisition_passive import (
    EUI_KAI_METRIC_TASK,
    knowledge_acquisition_passive_captures,
    observe_knowledge_acquisition_candidate,
)


def test_kai_passive_observer_is_noop_when_disabled():
    knowledge_acquisition_passive_captures.clear()

    capture = observe_knowledge_acquisition_candidate(
        enabled=False,
        reference=_reference(source_type="pdf"),
    )

    assert capture is None
    assert knowledge_acquisition_passive_captures.snapshot() == []


def test_kai_passive_observer_captures_candidate_success():
    knowledge_acquisition_passive_captures.clear()

    capture = observe_knowledge_acquisition_candidate(
        enabled=True,
        reference=_reference(
            source_type="pdf",
            supplied_extracted_text="worksheet text",
            educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
            educational_context_summary={"board": "CBSE", "grade": "6", "subject": "Science"},
        ),
    )

    assert capture is not None
    assert capture.status == "acquire_completed"
    assert capture.candidate is not None
    assert capture.candidate.authoritative is False
    assert knowledge_acquisition_passive_captures.snapshot()[-1] == capture
    assert f'task="{EUI_KAI_METRIC_TASK}",status="acquire_completed"' in (
        platform_metrics.prometheus_text()
    )


def test_kai_passive_observer_records_unsupported_source():
    knowledge_acquisition_passive_captures.clear()

    capture = observe_knowledge_acquisition_candidate(
        enabled=True,
        reference=_reference(source_type="image"),
    )

    assert capture is not None
    assert capture.status == "unsupported_input"
    assert capture.candidate is not None
    assert capture.candidate.review_status == "unsupported"


def test_kai_passive_observer_records_ambiguity():
    knowledge_acquisition_passive_captures.clear()

    capture = observe_knowledge_acquisition_candidate(
        enabled=True,
        reference=_reference(
            source_type="teacher_note",
            supplied_extracted_text="local note",
        ),
    )

    assert capture is not None
    assert capture.status == "ambiguous"
    assert capture.candidate is not None
    assert capture.candidate.trust_signals.ambiguity_count == 2


def test_kai_passive_observer_isolates_exceptions():
    class BrokenBuilder:
        def build(self, _reference):
            raise RuntimeError("synthetic KAI failure")

    capture = observe_knowledge_acquisition_candidate(
        enabled=True,
        reference=_reference(source_type="pdf"),
        builder=BrokenBuilder(),  # type: ignore[arg-type]
    )

    assert capture is None
    assert f'task="{EUI_KAI_METRIC_TASK}",status="acquire_failed"' in (
        platform_metrics.prometheus_text()
    )


def _reference(**kwargs) -> KnowledgeAcquisitionInputReference:
    payload = {"tenant_id": uuid.uuid4(), **kwargs}
    return KnowledgeAcquisitionInputReference(**payload)
