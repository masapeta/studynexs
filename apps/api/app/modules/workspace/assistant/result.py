"""Typed contract for the agentic assistant's result blocks (Phase 9 consolidation).

Every assistant turn returns ONE UI-independent block: a dict with a ``kind`` discriminator and
kind-specific fields, wrapped by ``handle_turn`` as ``{session_id, result_kind, block}`` and
consumed by ``AssistantBlockView.tsx``. Historically those blocks were untyped dicts assembled
across capabilities / composition / documents / workflows / actions. This module makes the shape
an authoritative, validated contract WITHOUT changing the wire representation or how blocks are
built — producers still return dicts; this validates them at the single return boundary.

Design constraints honoured:
* The models mirror the FIELDS THAT ACTUALLY EXIST in current payloads (inventoried from every
  producer), not assumptions.
* ``extra="allow"`` preserves any additional producer fields verbatim, so serialization never
  drops or reorders real data.
* Validation is a *compatibility check*, not a gate: ``validate_block`` never raises on a real
  turn — an unknown ``kind`` or a malformed-but-present payload falls back to a permissive model
  so a successful turn is never broken by schema drift in production. Tests, by contrast, assert
  strict conformance so drift is caught in CI.
"""

from __future__ import annotations

from typing import Any, Literal

import structlog
from pydantic import BaseModel, ConfigDict

logger = structlog.get_logger()

# The canonical set of result kinds the agentic assistant emits as a chat block.
RESULT_KINDS: frozenset[str] = frozenset(
    {
        "metrics",
        "table",
        "guide",
        "error",
        "clarify",
        "not_found",
        "document",
        "mixed",
        "navigate",
        "workflow",
        "action_preview",
    }
)


class _Block(BaseModel):
    """Permissive base: unknown/extra fields are kept verbatim so the wire shape is preserved."""

    model_config = ConfigDict(extra="allow")
    kind: str


class MetricItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    label: str
    value: str | int | float | None = None
    format: Literal["number", "money", "percent"] | None = None


class Column(BaseModel):
    model_config = ConfigDict(extra="allow")
    key: str
    label: str
    format: Literal["number", "money", "percent"] | None = None


class Citation(BaseModel):
    model_config = ConfigDict(extra="allow")
    title: str
    document_type: str | None = None
    snippet: str | None = None


class NavSuggestion(BaseModel):
    model_config = ConfigDict(extra="allow")
    label: str
    href: str


class ClarifyOption(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    label: str


class MetricsBlock(_Block):
    kind: Literal["metrics"] = "metrics"
    title: str | None = None
    subtitle: str | None = None
    source: str | None = None
    message: str | None = None
    metrics: list[MetricItem] = []
    href: str | None = None
    href_label: str | None = None


class TableBlock(_Block):
    kind: Literal["table"] = "table"
    title: str | None = None
    source: str | None = None
    columns: list[Column] = []
    rows: list[dict[str, Any]] = []
    empty_message: str | None = None
    href: str | None = None
    href_label: str | None = None


class GuideBlock(_Block):
    kind: Literal["guide"] = "guide"
    title: str | None = None
    message: str | None = None
    suggestions: list[NavSuggestion] = []


class ErrorBlock(_Block):
    kind: Literal["error"] = "error"
    title: str | None = None
    message: str | None = None


class ClarifyBlock(_Block):
    kind: Literal["clarify"] = "clarify"
    title: str | None = None
    message: str | None = None
    options: list[ClarifyOption] = []


class NotFoundBlock(_Block):
    kind: Literal["not_found"] = "not_found"
    title: str | None = None
    message: str | None = None


class DocumentBlock(_Block):
    kind: Literal["document"] = "document"
    title: str | None = None
    message: str | None = None
    citations: list[Citation] = []


class NavigateBlock(_Block):
    kind: Literal["navigate"] = "navigate"
    title: str | None = None
    href: str
    label: str | None = None


class MixedBlock(_Block):
    kind: Literal["mixed"] = "mixed"
    title: str | None = None
    data: dict[str, Any] | None = None       # a nested block (validated recursively if needed)
    document: dict[str, Any] | None = None    # a nested block or null


class WorkflowBlock(_Block):
    kind: Literal["workflow"] = "workflow"
    workflow_id: str
    title: str | None = None
    workflow_state: str | None = None
    summary: dict[str, Any] = {}
    actions: list[dict[str, Any]] = []
    message: str | None = None
    # Domain-status passthroughs (one per workflow; all optional — wraps, does not own).
    paper_status: str | None = None
    plan_status: str | None = None
    eval_status: str | None = None
    drafts: list[dict[str, Any]] | None = None


class ActionPreviewBlock(_Block):
    kind: Literal["action_preview"] = "action_preview"
    action: str
    title: str | None = None
    status: str | None = None
    preview: dict[str, Any] = {}
    confirm_action: dict[str, Any] = {}
    message: str | None = None


# Explicit dispatch by kind. A discriminated Pydantic union rejects unknown discriminator values
# outright, which would break a legitimately-new kind in production — so we dispatch by hand and
# fall back to the permissive base rather than relying on union discrimination.
_MODEL_BY_KIND: dict[str, type[_Block]] = {
    "metrics": MetricsBlock,
    "table": TableBlock,
    "guide": GuideBlock,
    "error": ErrorBlock,
    "clarify": ClarifyBlock,
    "not_found": NotFoundBlock,
    "document": DocumentBlock,
    "navigate": NavigateBlock,
    "mixed": MixedBlock,
    "workflow": WorkflowBlock,
    "action_preview": ActionPreviewBlock,
}


def validate_block(block: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    """Validate a result block against its typed model, returning the wire dict unchanged.

    Compatibility-first: in production (``strict=False``) a validation failure or unknown kind is
    logged (without sensitive payload data) and the ORIGINAL dict is returned, so a successful
    turn is never broken by schema drift. In tests (``strict=True``) a malformed KNOWN kind raises
    so drift is caught in CI.

    The returned value is the caller's original dict (not a model dump) — this guarantees the
    exact existing wire representation is preserved byte-for-byte; the model is used only to check
    conformance, never to reshape the response.
    """
    kind = block.get("kind")
    model = _MODEL_BY_KIND.get(kind) if isinstance(kind, str) else None
    if model is None:
        # Unknown/missing kind: never fail a turn on it; just note it for diagnosis.
        if strict and kind in RESULT_KINDS:
            raise AssertionError(f"no model registered for known kind {kind!r}")
        if not isinstance(kind, str):
            logger.warning("assistant_block_missing_kind")
        return block
    try:
        model.model_validate(block)
    except Exception as exc:  # noqa: BLE001 — validation must not break a real turn
        if strict:
            raise
        logger.warning("assistant_block_validation_failed", kind=kind, error=str(exc))
    return block
