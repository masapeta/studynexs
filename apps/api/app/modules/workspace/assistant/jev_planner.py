"""JEV (TypeSafe System One) planner backend — experimental, default-off.

The current Gemma planner returns a PlannerDecision (capability + params + temporal) in one LLM
call. JEV is a bounded-DECISION model (Choice/Noul/Score): it selects a capability and a temporal
category with calibrated confidence in one request, but it does NOT extract exact parameter
values. So this backend pairs:

  1. JEV Choice for the bounded fields (capability, temporal presence) — fast, confident, and
     the *only* thing JEV is asked to do; and
  2. DETERMINISTIC param extraction built entirely from existing pieces (admission-no regex,
     the fee-service class-label normalizer, the resolver's subject aliases, the temporal
     token/month tables) — no new LLM call on the accept path.

The HybridPlanner accepts the JEV decision when capability confidence >= a configured threshold,
otherwise falls back to the unchanged Gemma planner for the whole turn. Either way the output is a
standard PlannerDecision that feeds the FROZEN deterministic runtime (resolver, derivation,
temporal integrity, authorization, composition) — JEV never becomes the source of truth and never
bypasses a safety guard (spec §12).

This module adds a planning backend behind a flag; it changes none of the runtime components.
"""

from __future__ import annotations

import re
from typing import Any

import httpx
import structlog

from app.core.config import get_settings
from app.modules.workspace.assistant.planner import (
    PlannerDecision,
    TemporalIntent,
)
from app.modules.workspace.assistant.planner import (
    plan as gemma_plan,
)
from app.modules.workspace.assistant.tools import AssistantTool

logger = structlog.get_logger()

# JEV temporal categories -> the planner's TemporalIntent.presence vocabulary.
_TEMPORAL_CRITERIA = {
    "NONE": "no time frame mentioned",
    "CURRENT": "now, or an ongoing period that includes today (this month/week/year/term)",
    "PAST": "a period that ended before now (last month, in August, last year)",
    "FUTURE": "an upcoming period (next term)",
}

# Deterministic token tables — reused from the existing runtime (single source of truth), not
# reinvented here. Imported lazily to avoid import cycles at module load.
_ADMISSION_RE = re.compile(r"\b([A-Z]{2,4}\d{2,6})\b", re.IGNORECASE)
_THRESHOLD_RE = re.compile(r"(\d{1,3})\s*%")
_RELATIVE_PHRASES = {
    "today": "today", "yesterday": "yesterday",
    "this week": "this_week", "last week": "last_week",
    "this month": "this_month", "last month": "last_month",
    "this year": "this_year", "last year": "last_year",
    "this academic year": "current_academic_year",
    "previous academic year": "previous_academic_year",
    "last academic year": "previous_academic_year",
}


def _cap_criteria(tools: list[AssistantTool]) -> dict[str, str]:
    """Capability options for the JEV Choice, from the live catalog (first sentence of each
    tool description; no per-question tuning). Registered workflows are added as bounded options
    so JEV can route a workflow request (e.g. a question paper) as a first-class choice."""
    crit = {t.name: (t.description.split(".")[0][:120] or t.name) for t in tools}
    from app.modules.workspace.workflows.registry import list_workflows

    for wf in list_workflows():
        crit[f"{_WORKFLOW_PREFIX}{wf.workflow_id}"] = wf.description[:120]
    crit["unsupported"] = "The request is not answerable by any capability above"
    return crit


# JEV choice keys for workflows are namespaced so they never collide with capability names.
_WORKFLOW_PREFIX = "workflow:"


def _presence_for(category: str | None) -> str:
    if category in ("CURRENT", "PAST", "FUTURE"):
        return category
    return "NONE"


def _extract_time(text: str) -> Any | None:
    """Deterministic temporal token from text, reusing the runtime's own vocabulary.

    Returns a canonical relative token, a {"month": name} dict, or None. The authoritative
    temporal RESOLUTION + integrity guard still run downstream unchanged.
    """
    from app.modules.workspace.assistant.temporal import _MONTHS

    low = text.lower()
    for phrase, token in _RELATIVE_PHRASES.items():
        if phrase in low:
            return token
    for word in re.findall(r"[a-z]+", low):
        if word in _MONTHS:
            return {"month": word}
    return None


# A class reference span: "class/grade/std/year 10 A", "10A", "2 B", "Class 9". We isolate the
# SPAN first, then normalize only that — feeding a whole sentence into the label normalizer
# leaves stray words ("results for 10 a") that never match a real class (holdout root-cause).
_CLASS_SPAN_RE = re.compile(
    r"\b(?:class|grade|std|standard|year|div|division)\s*\d{1,2}\s*[a-e]?\b"
    r"|\b\d{1,2}\s*[a-e]\b",
    re.IGNORECASE,
)


def _extract_class_label(text: str) -> str | None:
    """Isolate a class reference span from free text, then normalize just that span."""
    from app.modules.fees.services.fee_service import _normalize_class_label

    m = _CLASS_SPAN_RE.search(text)
    if not m:
        return None
    return _normalize_class_label(m.group(0))


def _extract_params(text: str, tool: AssistantTool | None) -> dict[str, Any]:
    """Fill a capability's params from text using ONLY deterministic extractors.

    Never guesses: a param is set only when a token is unambiguously present. Downstream
    resolution/derivation/authorization validate every value (spec §12), so a missing param
    simply defers to derivation or an honest clarify — it is never fabricated.
    """
    from app.modules.workspace.assistant.resolver import _SUBJECT_ALIASES

    if tool is None:
        return {}
    accepted = set(tool.params)
    params: dict[str, Any] = {}

    if "student" in accepted:
        m = _ADMISSION_RE.search(text)
        if m:
            params["student"] = m.group(1).upper()

    if "class_label" in accepted:
        label = _extract_class_label(text)
        if label:
            params["class_label"] = label

    if "subject" in accepted:
        low = text.lower()
        for alias, canonical in _SUBJECT_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", low):
                params["subject"] = canonical
                break

    for pct_param in ("min_percent", "below_percent"):
        if pct_param in accepted:
            m = _THRESHOLD_RE.search(text)
            if m:
                params[pct_param] = float(m.group(1))

    if "time" in accepted:
        token = _extract_time(text)
        if token is not None:
            params["time"] = token

    return params


async def jev_decide(text: str, tools: list[AssistantTool]) -> dict[str, Any] | None:
    """One JEV request: capability + temporal category with confidence. None on any failure."""
    settings = get_settings()
    if not settings.TYPESAFE_API_KEY:
        return None
    body = {
        "state": text,
        "model": settings.TYPESAFE_MODEL,
        "questions": {
            "capability": {
                "type": "choice",
                "instructions": "Which capability best answers this school-assistant request?",
                "criteria": _cap_criteria(tools),
            },
            "temporal": {
                "type": "choice",
                "instructions": "What time frame does the request refer to?",
                "criteria": _TEMPORAL_CRITERIA,
            },
        },
    }
    try:
        async with httpx.AsyncClient(timeout=settings.AI_REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post(
                settings.TYPESAFE_URL,
                json=body,
                headers={"Authorization": f"Bearer {settings.TYPESAFE_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:  # noqa: BLE001 — any JEV failure degrades to Gemma fallback
        logger.warning("jev_planner_call_failed", error=str(exc))
        return None
    ans = data.get("answers", {})
    cap = ans.get("capability", {})
    return {
        "capability": cap.get("choice"),
        "confidence": cap.get("confidence", 0.0),
        "temporal": ans.get("temporal", {}).get("choice"),
        "usage": data.get("usage", {}),
    }


def jev_decision_to_plan(
    decision: dict[str, Any], text: str, tools: list[AssistantTool]
) -> PlannerDecision:
    """Turn a JEV bounded decision + deterministic params into a standard PlannerDecision."""
    from app.modules.workspace.assistant.tools import get_tool

    cap = decision.get("capability")
    if isinstance(cap, str) and cap.startswith(_WORKFLOW_PREFIX):
        return _jev_workflow_to_plan(cap[len(_WORKFLOW_PREFIX):], text)
    if not cap or cap == "unsupported" or cap not in {t.name for t in tools}:
        return PlannerDecision(action="clarify", message=None)
    tool = get_tool(cap)
    params = _extract_params(text, tool)
    presence = _presence_for(decision.get("temporal"))
    return PlannerDecision(
        route="STRUCTURED",
        action="tool",
        tool=cap,
        params=params,
        temporal=TemporalIntent(presence=presence, time=params.get("time")),
    )


def _jev_workflow_to_plan(workflow_id: str, text: str) -> PlannerDecision:
    """Build a workflow PlannerDecision from a JEV workflow choice + deterministic params.

    Params are extracted with the SAME deterministic extractors used for capabilities. Downstream
    the executor resolves and authorizes every value; a missing param defers to an honest clarify,
    never a fabricated one. Per-workflow: QP wants class/subject/marks; lesson plan wants
    class/subject; evaluation wants a student reference (exam + answer sheet come from the UI)."""
    from app.modules.workspace.assistant.resolver import _SUBJECT_ALIASES

    params: dict[str, Any] = {}
    low = text.lower()

    if workflow_id == "evaluate_answer_sheet":
        m = _ADMISSION_RE.search(text)
        if m:
            params["student"] = m.group(1).upper()
        return PlannerDecision(
            route="WORKFLOW", action="workflow", workflow_id=workflow_id, params=params
        )

    label = _extract_class_label(text)
    if label:
        params["class_label"] = label
    for alias, canonical in _SUBJECT_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", low):
            params["subject"] = canonical
            break
    if workflow_id != "lesson_plan":  # marks are meaningless for a lesson plan
        marks = re.search(r"(\d{1,3})\s*(?:marks?|mark)\b", low)
        if marks:
            params["total_marks"] = int(marks.group(1))
    return PlannerDecision(
        route="WORKFLOW", action="workflow", workflow_id=workflow_id, params=params
    )


async def plan_jev(
    text: str,
    *,
    tools: list[AssistantTool],
    history: list[dict[str, str]] | None = None,
    prev_state: dict[str, Any] | None = None,
) -> tuple[PlannerDecision, dict[str, Any]]:
    """JEV-only planning. Returns (decision, meta). Falls back to a clarify decision on failure
    (the hybrid, not this function, decides whether to call Gemma instead)."""
    decision = await jev_decide(text, tools)
    if decision is None:
        return PlannerDecision(action="clarify", message=None), {"jev_ok": False}
    plan_decision = jev_decision_to_plan(decision, text, tools)
    meta = {
        "jev_ok": True,
        "jev_capability": decision.get("capability"),
        "jev_confidence": decision.get("confidence"),
        "jev_temporal": decision.get("temporal"),
        "jev_usage": decision.get("usage"),
    }
    return plan_decision, meta


async def plan_hybrid(
    text: str,
    *,
    tools: list[AssistantTool],
    history: list[dict[str, str]] | None = None,
    prev_state: dict[str, Any] | None = None,
) -> tuple[PlannerDecision, dict[str, Any]]:
    """Hybrid: accept JEV when capability confidence >= threshold, else fall back to Gemma.

    A follow-up turn (history/prev_state present) always uses Gemma: conversational carry-over
    is owned by the deterministic ConversationSemanticState + Gemma prompt, and JEV has no view
    of prior turns here — so we never risk breaking carry-over (spec §6). Single-shot turns are
    where JEV's speed helps and where its bounded decision is well-posed.
    """
    settings = get_settings()
    threshold = settings.PLANNER_JEV_CONFIDENCE_THRESHOLD

    is_followup = bool(prev_state) or bool(history)
    if is_followup:
        decision = await gemma_plan(text, tools=tools, history=history, prev_state=prev_state)
        return decision, {"planner": "gemma", "reason": "followup", "fallback": True}

    jev = await jev_decide(text, tools)
    if jev is not None and (jev.get("confidence") or 0.0) >= threshold:
        cap = jev.get("capability")
        is_workflow = isinstance(cap, str) and cap.startswith(_WORKFLOW_PREFIX)
        if cap and cap != "unsupported" and (is_workflow or cap in {t.name for t in tools}):
            decision = jev_decision_to_plan(jev, text, tools)
            return decision, {
                "planner": "jev", "fallback": False,
                "jev_confidence": jev.get("confidence"),
                "jev_capability": cap, "jev_usage": jev.get("usage"),
            }

    # Uncertain, unsupported, or JEV unavailable -> Gemma handles the whole turn.
    decision = await gemma_plan(text, tools=tools, history=history, prev_state=prev_state)
    return decision, {
        "planner": "gemma", "fallback": True,
        "jev_confidence": (jev or {}).get("confidence"),
        "jev_capability": (jev or {}).get("capability"),
    }
