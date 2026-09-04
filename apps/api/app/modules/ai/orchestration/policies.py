"""Runtime policies for the Phase 0 workspace orchestration path."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.config import Settings, get_settings
from app.core.dependencies import CurrentUser


def _csv_values(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True)
class WorkspaceRuntimePolicy:
    orchestration_enabled: bool
    model_routing_enabled: bool
    cloud_fallback_enabled: bool
    action_tools_enabled: bool
    voice_enabled: bool
    max_tool_calls_per_turn: int
    max_model_calls_per_turn: int
    max_local_retry_count: int
    tool_timeout_ms: int
    tool_read_retry_count: int
    tool_circuit_breaker_threshold: int
    tool_circuit_breaker_cooldown_seconds: int
    max_input_chars: int
    enabled_portals: frozenset[str]
    enabled_roles: frozenset[str]
    enabled_schools: frozenset[str]
    allowed_report_types: frozenset[str]


def build_workspace_runtime_policy(
    *, settings: Settings | None = None,
) -> WorkspaceRuntimePolicy:
    runtime = settings or get_settings()
    return WorkspaceRuntimePolicy(
        orchestration_enabled=runtime.WORKSPACE_ORCHESTRATION_ENABLED,
        model_routing_enabled=runtime.WORKSPACE_MODEL_ROUTING_ENABLED,
        cloud_fallback_enabled=runtime.WORKSPACE_CLOUD_FALLBACK_ENABLED,
        action_tools_enabled=runtime.WORKSPACE_ACTION_TOOLS_ENABLED,
        voice_enabled=runtime.WORKSPACE_VOICE_ENABLED,
        max_tool_calls_per_turn=runtime.WORKSPACE_MAX_TOOL_CALLS_PER_TURN,
        max_model_calls_per_turn=runtime.WORKSPACE_MAX_MODEL_CALLS_PER_TURN,
        max_local_retry_count=runtime.WORKSPACE_MAX_LOCAL_RETRY_COUNT,
        tool_timeout_ms=runtime.WORKSPACE_TOOL_TIMEOUT_MS,
        tool_read_retry_count=runtime.WORKSPACE_TOOL_READ_RETRY_COUNT,
        tool_circuit_breaker_threshold=runtime.WORKSPACE_TOOL_CIRCUIT_BREAKER_THRESHOLD,
        tool_circuit_breaker_cooldown_seconds=(
            runtime.WORKSPACE_TOOL_CIRCUIT_BREAKER_COOLDOWN_SECONDS
        ),
        max_input_chars=runtime.WORKSPACE_MAX_INPUT_CHARS,
        enabled_portals=_csv_values(runtime.WORKSPACE_ENABLED_PORTALS),
        enabled_roles=_csv_values(runtime.WORKSPACE_ENABLED_ROLES),
        enabled_schools=_csv_values(runtime.WORKSPACE_ENABLED_SCHOOLS),
        allowed_report_types=_csv_values(runtime.WORKSPACE_ALLOWED_REPORT_TYPES),
    )


def enforce_workspace_access(
    current_user: CurrentUser,
    *,
    settings: Settings | None = None,
) -> WorkspaceRuntimePolicy:
    policy = build_workspace_runtime_policy(settings=settings)
    if not policy.orchestration_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if "teaching" not in policy.enabled_portals:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if current_user.role not in policy.enabled_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace access is not enabled for this role.",
        )
    if policy.enabled_schools and (
        current_user.school_id not in policy.enabled_schools
        and current_user.tenant_slug not in policy.enabled_schools
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return policy


def report_type_allowed(report_type: str, *, policy: WorkspaceRuntimePolicy) -> bool:
    return report_type in policy.allowed_report_types
