from __future__ import annotations

import pytest

from app.modules.ai.orchestration.policies import WorkspaceRuntimePolicy
from app.modules.ai.orchestration.router import route_workspace_read_turn


def _policy(
    *,
    model_routing_enabled: bool = False,
    cloud_fallback_enabled: bool = False,
) -> WorkspaceRuntimePolicy:
    return WorkspaceRuntimePolicy(
        orchestration_enabled=True,
        model_routing_enabled=model_routing_enabled,
        cloud_fallback_enabled=cloud_fallback_enabled,
        action_tools_enabled=False,
        voice_enabled=False,
        max_tool_calls_per_turn=3,
        max_model_calls_per_turn=2,
        max_local_retry_count=1,
        tool_timeout_ms=2500,
        tool_read_retry_count=1,
        tool_circuit_breaker_threshold=3,
        tool_circuit_breaker_cooldown_seconds=60,
        max_input_chars=6000,
        enabled_portals=frozenset({"teaching"}),
        enabled_roles=frozenset({"teacher", "class_incharge"}),
        enabled_schools=frozenset(),
        allowed_report_types=frozenset({"student_learning_evidence_report"}),
    )


def test_workspace_router_matches_known_learning_evidence_request() -> None:
    decision = route_workspace_read_turn(
        "show Test Student's learning report",
        policy=_policy(),
    )

    assert decision.strategy == "deterministic"
    assert decision.report_type == "student_learning_evidence_report"
    assert decision.student_selector == "Test Student"


@pytest.mark.parametrize(
    ("prompt", "expected_selector"),
    [
        ("Show learning evidence for Aarav in class 7A.", "Aarav"),
        ("Find student Riya and summarize her weak concepts.", "Riya"),
        (
            "Show recent assessment evidence for admission number 24017.",
            "24017",
        ),
    ],
)
def test_workspace_router_matches_phase0_starter_prompt_shapes(
    prompt: str,
    expected_selector: str,
) -> None:
    decision = route_workspace_read_turn(prompt, policy=_policy())

    assert decision.strategy == "deterministic"
    assert decision.report_type == "student_learning_evidence_report"
    assert decision.student_selector == expected_selector


def test_workspace_router_returns_unresolved_when_model_routing_disabled() -> None:
    decision = route_workspace_read_turn(
        "summarize my class performance",
        policy=_policy(),
    )

    assert decision.strategy == "unresolved"
    assert decision.student_selector is None


def test_workspace_router_defers_to_local_model_when_enabled() -> None:
    decision = route_workspace_read_turn(
        "summarize my class performance",
        policy=_policy(model_routing_enabled=True),
    )

    assert decision.strategy == "local_model"
    assert decision.report_type is None


def test_workspace_router_uses_cloud_fallback_after_local_failure() -> None:
    decision = route_workspace_read_turn(
        "summarize my class performance",
        policy=_policy(model_routing_enabled=True, cloud_fallback_enabled=True),
        local_model_failed=True,
    )

    assert decision.strategy == "cloud_fallback"
    assert decision.report_type is None
