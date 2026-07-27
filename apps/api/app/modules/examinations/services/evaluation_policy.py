"""Evaluation Policy layer for AEI v1.

Batch 4 converts deterministic academic reasoning into deterministic workflow
signals. It does not assign marks, score answers, integrate with the runtime
Evaluation Service, update UI, or change database schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.modules.examinations.schemas.academic_reasoning_result import AcademicReasoningResult
from app.modules.examinations.schemas.policy_decision import (
    PolicyDecision,
    PolicyDecisionStatus,
    PolicyTraceEntry,
)
from app.modules.examinations.services.subject_capability_registry import (
    CapabilityDescriptor,
    SubjectCapabilityRegistry,
)

DEFAULT_CONFIDENCE_THRESHOLD = 0.75


class EvaluationPolicy(Protocol):
    """Minimal Evaluation Policy contract for AEI Batch 4."""

    name: str

    def supports(self, reasoning: AcademicReasoningResult) -> bool:
        """Return whether this policy can evaluate the reasoning result."""
        ...

    def decide(self, reasoning: AcademicReasoningResult) -> PolicyDecision:
        """Return a workflow decision without marks or scoring."""
        ...


@dataclass(frozen=True)
class PolicyExecution:
    """A single policy execution decision."""

    policy: str
    supported: bool
    executed: bool
    decision: PolicyDecisionStatus | None = None
    metadata: dict[str, Any] | None = None

    @property
    def status(self) -> str:
        return "executed" if self.executed else "skipped"


class EvaluationPolicyEngine:
    """Orchestrates deterministic Evaluation Policies.

    The engine itself contains no subject-specific policy. It executes configured
    policies, then combines them conservatively:

    unsupported > manual_review > supported.
    """

    def __init__(self, policies: list[EvaluationPolicy] | None = None) -> None:
        self.policies = policies if policies is not None else default_policies()

    def decide(self, reasoning: AcademicReasoningResult) -> PolicyDecision:
        decisions: list[PolicyDecision] = []
        executions: list[PolicyExecution] = []

        for policy in self.policies:
            supported = policy.supports(reasoning)
            policy_decision: PolicyDecision | None = None
            trace_metadata: dict[str, Any] | None = None
            if supported:
                policy_decision = policy.decide(reasoning)
                decisions.append(policy_decision)
                trace_metadata = {
                    "manual_review_required": policy_decision.manual_review_required,
                    "capability_mode": policy_decision.capability_mode,
                }
            executions.append(
                PolicyExecution(
                    policy=policy.name,
                    supported=supported,
                    executed=supported,
                    decision=policy_decision.decision if policy_decision else None,
                    metadata=trace_metadata,
                )
            )

        result = _combine_policy_decisions(reasoning, decisions)
        return result.model_copy(update={"policy_trace": _trace_entries(executions)})


class CapabilityRegistryPolicy:
    """Maps reasoning capability to the Subject Capability Registry mode."""

    name = "capability_registry"

    def __init__(self, registry: SubjectCapabilityRegistry | None = None) -> None:
        self.registry = (
            registry if registry is not None else SubjectCapabilityRegistry.load_default()
        )

    def supports(self, reasoning: AcademicReasoningResult) -> bool:
        return True

    def decide(self, reasoning: AcademicReasoningResult) -> PolicyDecision:
        descriptor = self._resolve_descriptor(reasoning)
        decision = _decision_for_capability(descriptor)
        manual_review_required = decision != "supported"
        return PolicyDecision(
            decision=decision,
            manual_review_required=manual_review_required,
            supported_capability=descriptor.mode != "unsupported",
            capability_mode=descriptor.mode,
            confidence=_reasoning_confidence(reasoning),
            reason=_reason_for_descriptor(descriptor),
            explanations=_explanations(descriptor.description, reasoning.explanation),
            subject=reasoning.subject,
            capability=reasoning.capability,
            reasoning_type=reasoning.reasoning_type,
            metadata={"capability_descriptor": descriptor.as_dict()},
        )

    def _resolve_descriptor(self, reasoning: AcademicReasoningResult) -> CapabilityDescriptor:
        subject = reasoning.subject or ""
        capability = reasoning.capability or reasoning.reasoning_type
        return self.registry.resolve(subject, capability)


class ReasoningSignalPolicy:
    """Routes explicit reasoning uncertainty signals to manual review."""

    name = "reasoning_signal"

    def supports(self, reasoning: AcademicReasoningResult) -> bool:
        return bool(reasoning.review_signals) or reasoning.result == "not_applicable"

    def decide(self, reasoning: AcademicReasoningResult) -> PolicyDecision:
        signals = reasoning.review_signals or ("reasoning_not_applicable",)
        return PolicyDecision(
            decision="manual_review",
            manual_review_required=True,
            supported_capability=True,
            confidence=_reasoning_confidence(reasoning),
            reason="Reasoning produced uncertainty signals that require teacher review.",
            explanations=tuple(str(signal) for signal in signals),
            subject=reasoning.subject,
            capability=reasoning.capability,
            reasoning_type=reasoning.reasoning_type,
            metadata={"review_signals": list(signals), "reasoning_result": reasoning.result},
        )


class ConfidenceThresholdPolicy:
    """Routes low-confidence reasoning outputs to manual review."""

    name = "confidence_threshold"

    def __init__(self, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD) -> None:
        self.threshold = threshold

    def supports(self, reasoning: AcademicReasoningResult) -> bool:
        return _reasoning_confidence(reasoning) is not None

    def decide(self, reasoning: AcademicReasoningResult) -> PolicyDecision:
        confidence = _reasoning_confidence(reasoning)
        threshold = _confidence_threshold(reasoning, self.threshold)
        low_confidence = confidence is not None and confidence < threshold
        return PolicyDecision(
            decision="manual_review" if low_confidence else "supported",
            manual_review_required=low_confidence,
            supported_capability=True,
            confidence=confidence,
            reason=(
                "Reasoning confidence is below the manual-review threshold."
                if low_confidence
                else "Reasoning confidence meets the deterministic policy threshold."
            ),
            explanations=(f"confidence={confidence}", f"threshold={threshold}"),
            subject=reasoning.subject,
            capability=reasoning.capability,
            reasoning_type=reasoning.reasoning_type,
            metadata={"confidence": confidence, "threshold": threshold},
        )


def default_policies() -> list[EvaluationPolicy]:
    """Return the default AEI Batch 4 deterministic policy order."""

    return [
        CapabilityRegistryPolicy(),
        ReasoningSignalPolicy(),
        ConfidenceThresholdPolicy(),
    ]


def _combine_policy_decisions(
    reasoning: AcademicReasoningResult,
    decisions: list[PolicyDecision],
) -> PolicyDecision:
    if not decisions:
        return PolicyDecision(
            decision="manual_review",
            manual_review_required=True,
            supported_capability=False,
            reason="No deterministic AEI policy supported this reasoning result.",
            subject=reasoning.subject,
            capability=reasoning.capability,
            reasoning_type=reasoning.reasoning_type,
        )

    final_decision = _most_restrictive_decision(decisions)
    manual_review_required = final_decision != "supported"
    confidence = _minimum_confidence(decisions)
    capability_mode = _first_capability_mode(decisions)
    supported_capability = final_decision != "unsupported" and any(
        decision.supported_capability for decision in decisions
    )

    return PolicyDecision(
        decision=final_decision,
        manual_review_required=manual_review_required,
        supported_capability=supported_capability,
        capability_mode=capability_mode,
        confidence=confidence,
        reason=_combined_reason(final_decision, decisions),
        explanations=_unique_explanations(decisions),
        subject=reasoning.subject,
        capability=reasoning.capability,
        reasoning_type=reasoning.reasoning_type,
        metadata={
            "source_decisions": [
                {
                    "decision": decision.decision,
                    "manual_review_required": decision.manual_review_required,
                    "capability_mode": decision.capability_mode,
                    "reason": decision.reason,
                }
                for decision in decisions
            ]
        },
    )


def _trace_entries(executions: list[PolicyExecution]) -> tuple[PolicyTraceEntry, ...]:
    return tuple(
        PolicyTraceEntry(
            policy=execution.policy,
            status=execution.status,
            supported=execution.supported,
            decision=execution.decision,
            metadata=execution.metadata or {},
        )
        for execution in executions
    )


def _decision_for_capability(descriptor: CapabilityDescriptor) -> PolicyDecisionStatus:
    if descriptor.mode == "supported":
        return "supported"
    if descriptor.mode == "unsupported":
        return "unsupported"
    return "manual_review"


def _reason_for_descriptor(descriptor: CapabilityDescriptor) -> str:
    if descriptor.mode == "supported":
        return "Capability is supported by the AEI Subject Capability Registry."
    if descriptor.mode == "unsupported":
        return "Capability is unsupported by the AEI Subject Capability Registry."
    return "Capability is assistive or partial and requires teacher review."


def _explanations(*values: str | None) -> tuple[str, ...]:
    return tuple(value for value in values if value)


def _reasoning_confidence(reasoning: AcademicReasoningResult) -> float | None:
    value = reasoning.metadata.get("confidence")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, min(1.0, float(value)))
    return None


def _confidence_threshold(reasoning: AcademicReasoningResult, default: float) -> float:
    value = reasoning.metadata.get("confidence_threshold")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return max(0.0, min(1.0, float(value)))
    return default


def _most_restrictive_decision(decisions: list[PolicyDecision]) -> PolicyDecisionStatus:
    if any(decision.decision == "unsupported" for decision in decisions):
        return "unsupported"
    if any(decision.manual_review_required for decision in decisions):
        return "manual_review"
    return "supported"


def _minimum_confidence(decisions: list[PolicyDecision]) -> float | None:
    confidences = [
        decision.confidence for decision in decisions if decision.confidence is not None
    ]
    return min(confidences) if confidences else None


def _first_capability_mode(decisions: list[PolicyDecision]) -> str | None:
    for decision in decisions:
        if decision.capability_mode is not None:
            return decision.capability_mode
    return None


def _combined_reason(
    final_decision: PolicyDecisionStatus,
    decisions: list[PolicyDecision],
) -> str:
    for decision in decisions:
        if decision.decision == final_decision or decision.manual_review_required:
            return decision.reason
    return decisions[0].reason


def _unique_explanations(decisions: list[PolicyDecision]) -> tuple[str, ...]:
    values: list[str] = []
    seen: set[str] = set()
    for decision in decisions:
        for explanation in decision.explanations:
            if explanation not in seen:
                values.append(explanation)
                seen.add(explanation)
    return tuple(values)
