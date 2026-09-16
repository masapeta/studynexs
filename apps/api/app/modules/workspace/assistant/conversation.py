"""Conversational semantic state — carry-over for elliptical follow-ups (P1.2).

An elliptical follow-up ("what about September?", "his fees", "which of those…")
inherits the *unchanged* semantic dimensions of the previous turn and applies only
what the new turn explicitly changes (spec §1, §10). This is a GENERAL merge over a
structured state — never keyword handling of specific phrases (spec §26).

Design:
  - ConversationSemanticState is a compact, non-authoritative snapshot of a turn's meaning
    (domain / capability / entities / temporal). It is NOT an authorization token — every
    turn re-checks CurrentUser permissions downstream (spec §18) and it is tenant-scoped by
    living on tenant-scoped chat rows (spec §19).
  - The planner is told the previous state and returns, per dimension, either an explicit
    value or an "inherit" signal. A deterministic backstop then merges, which guarantees the
    P0.1 temporal invariant survives even if the LLM is sloppy (spec §12): a follow-up that
    doesn't override temporality keeps the previous temporality (incl. PAST).

The merge precedence is: explicit new-turn value > inherited previous value > default (§10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationSemanticState:
    """Compact, structured meaning of one turn, safe to persist and reuse."""

    domain: str | None = None            # fees / attendance / exams / students / teachers …
    capability: str | None = None        # the governed tool chosen (student_marks, …)
    action: str | None = None            # tool / compose / document / mixed
    entities: dict[str, str] = field(default_factory=dict)  # e.g. {"student": "ARM0218"}
    temporal_presence: str = "NONE"      # NONE/CURRENT/PAST/FUTURE/PERIOD/DATE_SPECIFIC
    temporal_time: Any | None = None     # canonical token/dict for the resolver
    subject: str | None = None           # exam subject, when relevant
    # Semantic intent of the turn, independent of tool naming (P1.2a). ``operation`` is the
    # broad action (collection / lookup / ranking / list …); ``metric`` is the measure asked
    # for (amount / receipt_count / percentage / count …). These let an elliptical metric
    # switch ("how many receipts?") keep the domain+operation+time and change only the metric.
    operation: str | None = None
    metric: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "capability": self.capability,
            "action": self.action,
            "entities": dict(self.entities),
            "temporal_presence": self.temporal_presence,
            "temporal_time": self.temporal_time,
            "subject": self.subject,
            "operation": self.operation,
            "metric": self.metric,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ConversationSemanticState | None":
        if not data:
            return None
        return cls(
            domain=data.get("domain"),
            capability=data.get("capability"),
            action=data.get("action"),
            entities=dict(data.get("entities") or {}),
            temporal_presence=data.get("temporal_presence") or "NONE",
            temporal_time=data.get("temporal_time"),
            subject=data.get("subject"),
            operation=data.get("operation"),
            metric=data.get("metric"),
        )


# Capability -> the semantic domain it belongs to. Used to decide when a follow-up stays
# in the same domain (inherit temporal/entity) vs. switches domain (drop stale dimensions).
_CAPABILITY_DOMAIN = {
    "student_attendance": "attendance",
    "class_attendance_today": "attendance",
    "low_attendance_students": "attendance",
    "fee_collection": "fees",
    "fee_collection_period": "fees",
    "students_fee_pending_over": "fees",
    "student_fees": "fees",
    "student_marks": "exams",
    "class_results": "exams",
    "subject_toppers": "exams",
    "student_profile": "students",
    "class_roster": "students",
    "teachers_for_class": "teachers",
    "teacher_assignments": "teachers",
    "staff_directory": "staff",
    "school_overview": "overview",
}

# Entity keys that identify "who/what" a turn is about — eligible for inheritance.
_ENTITY_KEYS = ("student", "student_id", "class_label", "class", "teacher", "teacher_id")

# Which entity keys each capability actually accepts — so we never inject a per-student
# entity into a school-wide capability (e.g. fee_collection_period takes no student).
_CAPABILITY_ENTITY_PARAMS = {
    "student_attendance": {"student", "student_id"},
    "student_profile": {"student", "student_id"},
    "student_fees": {"student", "student_id"},
    "student_marks": {"student", "student_id"},
    "class_roster": {"class_label", "class"},
    "class_attendance_today": {"class_label", "class"},
    "class_results": {"class_label", "class"},
    "subject_toppers": {"class_label", "class"},
    "low_attendance_students": {"class_label", "class"},
    "students_fee_pending_over": {"class_label", "class"},
    "teachers_for_class": {"class_label", "class"},
    "teacher_assignments": {"teacher", "teacher_id"},
    # fee_collection / fee_collection_period / school_overview / staff_directory: no entity.
}


def domain_for_capability(capability: str | None) -> str | None:
    return _CAPABILITY_DOMAIN.get(capability or "")


def state_from_decision(decision: Any) -> ConversationSemanticState:
    """Capture the semantic state a completed turn established (for persistence)."""
    params = getattr(decision, "params", {}) or {}
    temporal = getattr(decision, "temporal", None)
    entities = {k: str(params[k]) for k in _ENTITY_KEYS if params.get(k)}
    return ConversationSemanticState(
        domain=domain_for_capability(getattr(decision, "tool", None))
        or (getattr(decision, "route", None) or "").lower() or None,
        capability=getattr(decision, "tool", None),
        action=getattr(decision, "action", None),
        entities=entities,
        temporal_presence=getattr(temporal, "presence", "NONE") if temporal else "NONE",
        temporal_time=getattr(temporal, "time", None) if temporal else None,
        subject=params.get("subject"),
        operation=getattr(decision, "operation", None),
        metric=getattr(decision, "metric", None),
    )


# Metric words -> the capability that surfaces them, per domain. Used to recover an
# elliptical metric switch when the LLM failed to pick a tool but the topic is clear
# (general operation/metric inheritance, not a phrase-specific patch — P1.2a).
_DOMAIN_DEFAULT_CAPABILITY = {
    "fees": "fee_collection_period",
    "attendance": "student_attendance",
    "exams": "student_marks",
}


def merge_follow_up(
    prev: ConversationSemanticState | None, decision: Any
) -> tuple[Any, dict[str, Any]]:
    """Deterministically merge a follow-up decision with the previous state.

    Mutates ``decision`` in place (params + temporal) and returns (decision, trace). The LLM
    proposes; this backstop guarantees the precedence rule (§10) and the P0.1 temporal
    invariant (§12) hold regardless of LLM diligence. It NEVER invents domains or entities:
    inheritance only fills a dimension the new turn left blank AND only when the follow-up
    stays in the same domain (or explicitly reuses the entity).
    """
    trace: dict[str, Any] = {"inherited": [], "prev_domain": prev.domain if prev else None}
    if prev is None:
        return decision, trace

    params = dict(getattr(decision, "params", {}) or {})
    temporal = getattr(decision, "temporal", None)
    new_domain = domain_for_capability(getattr(decision, "tool", None))

    # A turn is "elliptical" when it names no entity of its own — a strong signal it is
    # continuing the previous subject rather than starting fresh.
    new_has_entity = any(params.get(k) for k in _ENTITY_KEYS)
    same_domain = new_domain is not None and new_domain == prev.domain

    # 0) Capability recovery (P1.2a): a metric-only follow-up ("how many receipts?") often
    #    makes the LLM drop the tool (guide/clarify) even though the topic is unchanged. If
    #    this turn chose no tool, named no entity, and expressed a new metric/operation while
    #    the previous turn had a capability, inherit that capability so the topic survives.
    #    This is general operation/metric continuation — never a phrase-specific rule.
    new_metric = getattr(decision, "metric", None)
    new_operation = getattr(decision, "operation", None)
    if (
        getattr(decision, "action", None) not in ("tool", "compose")
        and not new_has_entity
        and prev.capability
        and (new_metric or new_operation)
    ):
        inferred = prev.capability
        # If only a metric changed and prev domain has a canonical metric capability, prefer it.
        if prev.domain in _DOMAIN_DEFAULT_CAPABILITY and not new_operation:
            inferred = prev.capability or _DOMAIN_DEFAULT_CAPABILITY[prev.domain]
        decision.tool = inferred
        decision.action = "tool"
        decision.route = "STRUCTURED"
        new_domain = domain_for_capability(inferred)
        same_domain = new_domain is not None and new_domain == prev.domain
        trace["inherited"].append("capability")

    # 1) Entity inheritance: if the new turn names no entity, inherit the prior entity —
    #    but only into a capability that ACCEPTS that entity param (never inject a student
    #    into a school-wide tool like fee_collection_period). Domains must be compatible.
    _entity_domains = {"fees", "exams", "attendance", "students"}
    accepted = _CAPABILITY_ENTITY_PARAMS.get(getattr(decision, "tool", "") or "", set())
    if not new_has_entity and prev.entities and accepted and (
        same_domain or new_domain in _entity_domains
    ):
        for k, v in prev.entities.items():
            if k in accepted and not params.get(k):
                params[k] = v
                trace["inherited"].append(f"entity:{k}")

    # 2) Subject inheritance (exams): "what about English" keeps the student, swaps subject;
    #    but if the new turn changed nothing about subject and stays in exams, keep prior.
    if new_domain == "exams" and prev.subject and not params.get("subject") and same_domain:
        params["subject"] = prev.subject
        trace["inherited"].append("subject")

    # 3) Temporal inheritance (the critical P0.1-preserving path, §11/§12):
    #    if the new turn did not express its own temporality, inherit the previous turn's —
    #    including PAST. This is what stops "what about September?" from silently going
    #    current, and stops a historical follow-up from becoming current-state.
    if temporal is not None:
        new_presence = (temporal.presence or "NONE").upper()
        new_time = temporal.time
        if new_presence == "NONE" and new_time is None and prev.temporal_presence != "NONE":
            temporal.presence = prev.temporal_presence
            temporal.time = prev.temporal_time
            trace["inherited"].append("temporal:full")
            # Restore the window into params so the PLAN actually applies it (not just the
            # semantic layer) — otherwise the integrity guard sees a dropped concrete window.
            if prev.temporal_time is not None and "time" not in params:
                params["time"] = prev.temporal_time
        elif new_time is not None and new_presence == "NONE" and prev.temporal_presence == "PAST":
            # New concrete window but presence unstated + prior was historical -> stay PAST
            # (e.g. historical August -> "September" must remain historical September, §5/§11).
            temporal.presence = "PAST"
            trace["inherited"].append("temporal:presence")

    # 4) Operation inheritance (P1.2a): a metric-only follow-up keeps the previous operation
    #    (e.g. 'collection') so the intent stays coherent; the metric is whatever the new turn
    #    asked for, falling back to the previous metric when unspecified.
    if same_domain and prev.operation and not getattr(decision, "operation", None):
        decision.operation = prev.operation
        trace["inherited"].append("operation")
    if same_domain and prev.metric and not getattr(decision, "metric", None):
        decision.metric = prev.metric
        trace["inherited"].append("metric")

    decision.params = params
    trace["merged_entities"] = {k: params.get(k) for k in _ENTITY_KEYS if params.get(k)}
    trace["merged_temporal"] = {
        "presence": getattr(temporal, "presence", "NONE") if temporal else "NONE",
        "time": getattr(temporal, "time", None) if temporal else None,
    }
    trace["merged_operation"] = getattr(decision, "operation", None)
    trace["merged_metric"] = getattr(decision, "metric", None)
    return decision, trace
