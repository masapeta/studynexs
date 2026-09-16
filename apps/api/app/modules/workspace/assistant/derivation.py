"""Parameter derivation from canonical relationships (P1.3).

When a follow-up pivots to a capability that needs a parameter the conversation doesn't yet
have explicitly (e.g. "who scored highest?" -> subject_toppers needs class_label, but context
only holds student=ARM0242), derive the missing parameter through an AUTHORITATIVE ERP
relationship (student -> belongs_to -> class) rather than asking the user (spec §1, §22).

Principles:
  - Authoritative source only (§4): derivations resolve real ERP records via the resolver /
    services, never the LLM or NL wording.
  - Canonical ids where possible (§5); the resolver already carries the student's class label.
  - Precedence EXPLICIT > INHERITED > DERIVED > DEFAULT (§25). We only fill a required param that
    is still MISSING after explicit+inherited merge; we never overwrite a provided value (§26).
  - Bounded depth (§13): a small registry of one-hop relationships, composed at most twice.
  - Deterministic (§14): a unique relationship derives; ambiguous/unavailable -> no guess.
  - Derivation does NOT authorize (§11): it only fills params; the capability's own P1.1
    authorization runs afterwards (derive -> authorize -> execute).
  - Historical safety (§15): derivation feeds CURRENT relationships; the P0/P0.1 guards still
    block a historical request downstream regardless of what we derived.
  - Provenance recorded for observability (§8, §28); never surfaced to end users.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspace.assistant.resolver import resolve_student

# Parameter sources (provenance).
SRC_EXPLICIT = "EXPLICIT"
SRC_INHERITED = "INHERITED"
SRC_DERIVED = "DERIVED"
SRC_DEFAULT = "SAFE_DEFAULT"
SRC_UNAVAILABLE = "UNAVAILABLE"

# Required parameters per capability that are eligible for derivation when missing. Only
# capabilities whose missing param can be derived from an in-context entity are listed; others
# keep their existing clarify/not_found behaviour. This is the generic requirement registry
# (§6) — not per-capability bespoke code.
CAPABILITY_REQUIRES: dict[str, list[str]] = {
    "subject_toppers": ["class_label", "subject"],
    "class_results": ["class_label"],
    "class_roster": ["class_label"],
    "class_attendance_today": ["class_label"],
    "teachers_for_class": ["class_label"],  # optional in the cap, but derivable when a
                                            # follow-up pivots "who teaches his class?"
}


async def _derive_class_label_from_student(
    db: AsyncSession, school_id: uuid.UUID, student_token: str
) -> tuple[str | None, dict[str, Any] | None]:
    """student -> belongs_to -> class_label, from the authoritative student record.

    Returns (class_label, provenance) or (None, None) when the student is missing/ambiguous
    (deterministic: no guess, §14). Reuses resolve_student whose ResolvedEntity already
    carries the class label from the Student->Class join.
    """
    res = await resolve_student(db, school_id, student_token)
    if res.is_empty or res.is_ambiguous:
        return None, None
    entity = res.one
    class_label = (entity.detail or {}).get("class_label")
    if not class_label:
        return None, None
    return class_label, {
        "entity_type": "student",
        "entity_id": (entity.detail or {}).get("admission_no") or student_token,
        "relationship": "belongs_to",
        "to": "class",
    }


async def derive_parameters(
    db: AsyncSession,
    school_id: uuid.UUID,
    decision: Any,
    prev_state: Any,
    *,
    trace: dict[str, Any] | None = None,
) -> None:
    """Fill missing REQUIRED params for the chosen capability from canonical relationships.

    Runs after conversational merge (explicit + inherited already applied to params) and
    before execution. Mutates decision.params in place; records provenance in trace. Never
    overrides an explicitly-provided value (§26). Bounded, deterministic, authoritative.
    """
    tool = getattr(decision, "tool", None)
    if getattr(decision, "action", None) != "tool" or not tool:
        return
    required = CAPABILITY_REQUIRES.get(tool)
    if not required:
        return

    params = dict(getattr(decision, "params", {}) or {})
    provenance: list[dict[str, Any]] = []

    # A student we can derive from: explicit in this turn, else inherited from prior context.
    student_token = (
        params.get("student")
        or params.get("student_id")
        or (getattr(prev_state, "entities", {}) or {}).get("student")
        or (getattr(prev_state, "entities", {}) or {}).get("student_id")
    )

    for param in required:
        if params.get(param):
            continue  # EXPLICIT/INHERITED already present — never override (§25/§26)
        if param == "class_label" and student_token:
            class_label, derived_from = await _derive_class_label_from_student(
                db, school_id, str(student_token)
            )
            if class_label:
                params[param] = class_label
                provenance.append({
                    "parameter": param, "value": class_label,
                    "source": SRC_DERIVED, "derived_from": derived_from,
                })

    decision.params = params
    if trace is not None and provenance:
        trace["param_provenance"] = provenance
