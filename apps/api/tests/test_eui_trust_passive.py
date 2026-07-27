"""EUI Phase 6 - passive Trust Report observer."""

from __future__ import annotations

import uuid

from app.modules.eui.schemas.educational_context import (
    EducationalContext,
    EducationalContextProvenance,
)
from app.modules.eui.schemas.trust_report import TrustReport
from app.modules.eui.services.trust_report_passive import (
    observe_trust_report,
    trust_report_passive_captures,
)


def test_trust_report_passive_observer_is_noop_when_disabled():
    trust_report_passive_captures.clear()

    capture = observe_trust_report(enabled=False, subject=_context())

    assert capture is None
    assert trust_report_passive_captures.snapshot() == []


def test_trust_report_passive_observer_captures_report_when_enabled():
    trust_report_passive_captures.clear()

    capture = observe_trust_report(enabled=True, subject=_context())

    assert capture is not None
    assert capture.status == "completed"
    assert isinstance(capture.report, TrustReport)
    assert capture.report.overall_posture == "trusted"
    assert trust_report_passive_captures.snapshot()[-1] == capture


def test_trust_report_passive_observer_isolates_exceptions():
    class BrokenBuilder:
        def build_for_context(self, context):  # noqa: ANN001, ANN201
            raise RuntimeError("boom")

    trust_report_passive_captures.clear()

    capture = observe_trust_report(
        enabled=True,
        subject=_context(),
        builder=BrokenBuilder(),  # type: ignore[arg-type]
    )

    assert capture is None
    stored = trust_report_passive_captures.snapshot()[-1]
    assert stored.status == "failed"
    assert stored.error == "boom"


def _context() -> EducationalContext:
    return EducationalContext(
        tenant_id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
        resolution_status="resolved",
        board="CBSE",
        grade="6",
        subject="Science",
        educational_identity_id="ei://cbse/ncf2023/g6/science/ch05",
        field_sources={"grade": "educational_identity"},
        provenance=EducationalContextProvenance(
            source="context_resolver",
            resolved_from="educational_identity",
        ),
    )
