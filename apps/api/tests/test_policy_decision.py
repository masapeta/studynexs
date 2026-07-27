import pytest
from pydantic import ValidationError

from app.modules.examinations.schemas.policy_decision import PolicyDecision, PolicyTraceEntry


def test_policy_decision_is_assignment_protected():
    decision = PolicyDecision(
        decision="supported",
        manual_review_required=False,
        supported_capability=True,
        reason="Capability is supported.",
    )

    with pytest.raises(ValidationError):
        decision.decision = "manual_review"

    assert decision.decision == "supported"


def test_policy_decision_nested_metadata_is_read_only():
    decision = PolicyDecision(
        decision="manual_review",
        manual_review_required=True,
        supported_capability=True,
        reason="Teacher review required.",
        metadata={"source": "policy"},
    )

    with pytest.raises(TypeError):
        decision.metadata["source"] = "mutated"

    assert decision.metadata["source"] == "policy"


def test_policy_decision_rejects_unknown_top_level_fields():
    with pytest.raises(ValidationError):
        PolicyDecision(
            decision="supported",
            manual_review_required=False,
            supported_capability=True,
            reason="Capability is supported.",
            marks=1,
        )


def test_policy_decision_validates_confidence_bounds():
    with pytest.raises(ValidationError):
        PolicyDecision(
            decision="manual_review",
            manual_review_required=True,
            supported_capability=True,
            confidence=1.5,
            reason="Invalid confidence.",
        )


def test_policy_decision_serializes_trace_stably():
    original = PolicyDecision(
        decision="manual_review",
        manual_review_required=True,
        supported_capability=True,
        capability_mode="assist",
        confidence=0.6,
        reason="Teacher review required.",
        policy_trace=(
            PolicyTraceEntry(
                policy="confidence_threshold",
                status="executed",
                supported=True,
                decision="manual_review",
                metadata={"threshold": 0.75},
            ),
        ),
    )

    restored = PolicyDecision.model_validate_json(original.model_dump_json())

    assert restored == original
    assert restored.policy_trace[0].status == "executed"
    assert restored.policy_trace[0].decision == "manual_review"
    assert restored.policy_trace[0].metadata["threshold"] == 0.75


def test_policy_trace_entry_rejects_invalid_status():
    with pytest.raises(ValidationError):
        PolicyTraceEntry(policy="x", status="available", supported=True)
