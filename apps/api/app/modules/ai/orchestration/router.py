"""Zero-model-first routing for the Phase 0 teacher workspace."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import ConfigDict

from app.modules.ai.orchestration.policies import WorkspaceRuntimePolicy, report_type_allowed
from app.modules.workspace.schemas.response import WorkspaceSchemaModel

_REPORT_TYPE = "student_learning_evidence_report"
_ROUTE_PATTERNS = (
    re.compile(
        r"^show\s+(?P<selector>.+?)'s\s+(?:learning\s+report|mastery\s+evidence)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^show\s+(?P<selector>.+?)\s+(?:learning\s+report|mastery\s+evidence)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^show\s+weak\s+concepts\s+for\s+(?P<selector>.+?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^show\s+learning\s+evidence\s+for\s+(?P<selector>.+?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^show\s+recent\s+assessment\s+evidence\s+for\s+(?P<selector>.+?)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^find\s+student\s+(?P<selector>.+?)\s+and\s+summarize\s+(?:their|his|her)\s+weak\s+concepts$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^why\s+is\s+(?P<selector>.+?)\s+weak\s+in\s+.+$",
        re.IGNORECASE,
    ),
)


class WorkspaceRouteDecision(WorkspaceSchemaModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Literal["deterministic", "local_model", "cloud_fallback", "unresolved"]
    report_type: Literal["student_learning_evidence_report"] | None = None
    student_selector: str | None = None
    detail: str


def _normalize_query(text: str) -> str:
    return " ".join(text.split()).strip().rstrip(".?!")


def _clean_selector(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().rstrip(".?!")
    cleaned = re.sub(r"^admission\s+(?:number|no\.?)\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+in\s+class\s+.+$", "", cleaned, flags=re.IGNORECASE)
    return cleaned or None


def route_workspace_read_turn(
    text: str,
    *,
    policy: WorkspaceRuntimePolicy,
    local_model_failed: bool = False,
) -> WorkspaceRouteDecision:
    normalized = _normalize_query(text)
    for pattern in _ROUTE_PATTERNS:
        match = pattern.match(normalized)
        if not match:
            continue
        selector = _clean_selector(match.group("selector"))
        if selector is None:
            break
        if not report_type_allowed(_REPORT_TYPE, policy=policy):
            return WorkspaceRouteDecision(
                strategy="unresolved",
                detail="The configured workspace report allowlist does not permit this report.",
            )
        return WorkspaceRouteDecision(
            strategy="deterministic",
            report_type=_REPORT_TYPE,
            student_selector=selector,
            detail="Matched the deterministic student learning evidence report route.",
        )

    if local_model_failed and policy.cloud_fallback_enabled:
        return WorkspaceRouteDecision(
            strategy="cloud_fallback",
            detail="Deterministic routing failed and cloud fallback is allowed for normalization.",
        )

    if policy.model_routing_enabled:
        return WorkspaceRouteDecision(
            strategy="local_model",
            detail="Deterministic routing did not match; local-model normalization is allowed.",
        )

    return WorkspaceRouteDecision(
        strategy="unresolved",
        detail="The request does not match the first supported deterministic workspace report.",
    )
