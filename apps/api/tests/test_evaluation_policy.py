from app.modules.examinations.schemas.academic_reasoning_result import AcademicReasoningResult
from app.modules.examinations.services.evaluation_policy import (
    CapabilityRegistryPolicy,
    ConfidenceThresholdPolicy,
    EvaluationPolicyEngine,
    ReasoningSignalPolicy,
    default_policies,
)


def _reasoning(
    *,
    subject: str = "mathematics",
    capability: str = "numeric_equivalence",
    reasoning_type: str = "numeric_equivalence",
    result: str = "equivalent",
    explanation: str = "The answer is equivalent.",
    metadata: dict | None = None,
    review_signals: tuple[str, ...] = (),
) -> AcademicReasoningResult:
    return AcademicReasoningResult(
        reasoning_type=reasoning_type,
        result=result,
        subject=subject,
        capability=capability,
        explanation=explanation,
        review_signals=review_signals,
        metadata=metadata or {},
    )


def test_default_policy_order_is_stable():
    policies = default_policies()

    assert [policy.name for policy in policies] == [
        "capability_registry",
        "reasoning_signal",
        "confidence_threshold",
    ]
    assert isinstance(policies[0], CapabilityRegistryPolicy)
    assert isinstance(policies[1], ReasoningSignalPolicy)
    assert isinstance(policies[2], ConfidenceThresholdPolicy)


def test_supported_math_capability_does_not_require_manual_review():
    decision = EvaluationPolicyEngine().decide(_reasoning())

    assert decision.decision == "supported"
    assert decision.manual_review_required is False
    assert decision.supported_capability is True
    assert decision.capability_mode == "supported"
    assert decision.reasoning_type == "numeric_equivalence"
    assert "marks" not in decision.model_dump()


def test_assist_mode_routes_to_manual_review_without_scoring():
    decision = EvaluationPolicyEngine().decide(
        _reasoning(
            subject="chemistry",
            capability="reaction_balancing",
            reasoning_type="reaction_balancing",
            result="balanced",
            explanation="The chemical equation is balanced.",
        )
    )

    assert decision.decision == "manual_review"
    assert decision.manual_review_required is True
    assert decision.supported_capability is True
    assert decision.capability_mode == "assist"
    assert "teacher review" in decision.reason.lower()
    assert "marks" not in decision.model_dump()


def test_checklist_mode_routes_to_manual_review():
    decision = EvaluationPolicyEngine().decide(
        _reasoning(
            subject="biology",
            capability="diagrams",
            reasoning_type="visual_checklist",
            result="checklist",
            explanation="Checklist observations were interpreted.",
        )
    )

    assert decision.decision == "manual_review"
    assert decision.manual_review_required is True
    assert decision.supported_capability is True
    assert decision.capability_mode == "checklist"


def test_unknown_capability_is_unsupported_and_requires_manual_review():
    decision = EvaluationPolicyEngine().decide(
        _reasoning(
            subject="mathematics",
            capability="unknown_capability",
            reasoning_type="unknown",
            result="interpreted",
        )
    )

    assert decision.decision == "unsupported"
    assert decision.manual_review_required is True
    assert decision.supported_capability is False
    assert decision.capability_mode == "unsupported"


def test_review_signals_upgrade_supported_capability_to_manual_review():
    decision = EvaluationPolicyEngine().decide(
        _reasoning(
            review_signals=("numeric_parse_failed",),
            result="not_applicable",
            explanation="The answer could not be interpreted.",
        )
    )

    assert decision.decision == "manual_review"
    assert decision.manual_review_required is True
    assert decision.supported_capability is True
    assert "numeric_parse_failed" in decision.explanations


def test_low_confidence_routes_supported_capability_to_manual_review():
    decision = EvaluationPolicyEngine().decide(
        _reasoning(metadata={"confidence": 0.42, "confidence_threshold": 0.8})
    )

    assert decision.decision == "manual_review"
    assert decision.manual_review_required is True
    assert decision.supported_capability is True
    assert decision.confidence == 0.42
    assert "confidence=0.42" in decision.explanations
    assert "threshold=0.8" in decision.explanations


def test_high_confidence_preserves_supported_decision():
    decision = EvaluationPolicyEngine().decide(
        _reasoning(metadata={"confidence": 0.93, "confidence_threshold": 0.8})
    )

    assert decision.decision == "supported"
    assert decision.manual_review_required is False
    assert decision.confidence == 0.93


def test_policy_trace_records_executed_and_skipped_policies():
    decision = EvaluationPolicyEngine().decide(_reasoning())

    trace = [entry.model_dump() for entry in decision.policy_trace]
    assert {
        "policy": "capability_registry",
        "status": "executed",
        "supported": True,
        "decision": "supported",
        "metadata": {
            "manual_review_required": False,
            "capability_mode": "supported",
        },
    } in trace
    assert {
        "policy": "reasoning_signal",
        "status": "skipped",
        "supported": False,
        "decision": None,
        "metadata": {},
    } in trace
    assert {
        "policy": "confidence_threshold",
        "status": "skipped",
        "supported": False,
        "decision": None,
        "metadata": {},
    } in trace
