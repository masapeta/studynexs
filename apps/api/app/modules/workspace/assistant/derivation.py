"""Parameter derivation from canonical relationships (P1.3, generalized in P1.5).

When a capability needs a parameter the conversation doesn't have explicitly (e.g.
subject_toppers needs a class, but context only holds student=ARM0242), derive it through an
AUTHORITATIVE ERP relationship (student -belongs_to-> class) instead of asking (spec §1, §22).

P1.5: this engine is GENERIC — it reads the Capability Contract + Relationship registries
(contracts.py) rather than per-capability branches. For each required+derivable, still-missing
param it finds a bounded relationship path from a known context entity to the param's entity
type and runs the relationship resolver.

Invariants preserved from P1.3:
  - Authoritative source only (§4); canonical resolution (§5); deterministic — ambiguous or
    missing yields no value, no guess (§14).
  - Precedence EXPLICIT > INHERITED > DERIVED > DEFAULT (§19); never overwrite a provided
    value (§26).
  - Bounded depth (§10), cycle-free.
  - Derivation does NOT authorize (§21): capabilities run their P1.1 checks afterwards.
  - Historical safety (§20): the caller skips derivation for PAST requests; relationships also
    declare temporal_mode.
  - Provenance recorded for observability (§18, §30).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspace.assistant.contracts import (
    SRC_DERIVED,
    SRC_EXPLICIT,
    SRC_INHERITED,
    SRC_UNAVAILABLE,
    find_relationship,
    get_contract,
)

__all__ = [
    "derive_parameters", "SRC_DERIVED", "SRC_EXPLICIT", "SRC_INHERITED", "SRC_UNAVAILABLE",
]

# Max relationship hops when deriving one parameter (§10). student->class = 1.
MAX_DERIVATION_DEPTH = 2

# Context entity keys we may derive FROM, mapped to their canonical entity type.
_CONTEXT_ENTITY_TYPES = {
    "student": "student", "student_id": "student",
    "class_label": "class", "class": "class",
    "teacher": "teacher", "teacher_id": "teacher",
}


def _known_entities(params: dict[str, Any], prev_state: Any) -> dict[str, str]:
    """Canonical entity type -> token, from explicit params then inherited context."""
    known: dict[str, str] = {}
    prev_entities = (getattr(prev_state, "entities", {}) or {}) if prev_state else {}
    for key, etype in _CONTEXT_ENTITY_TYPES.items():
        val = params.get(key) or prev_entities.get(key)
        if val and etype not in known:
            known[etype] = str(val)
    return known


async def _derive_one(
    db: AsyncSession,
    school_id: uuid.UUID,
    target_type: str,
    derive_from: tuple[str, ...],
    known: dict[str, str],
    *,
    cache: dict[tuple[str, str], tuple[str | None, dict | None]],
) -> tuple[str | None, dict | None]:
    """Find a bounded relationship path from a known source entity to target_type; resolve it.

    Single-hop today via the registry; the shape admits a second hop within
    MAX_DERIVATION_DEPTH without per-relationship code.
    """
    for src_entity in derive_from:
        token = known.get(src_entity)
        if not token:
            continue
        rel = find_relationship(src_entity, target_type)
        if rel is None:
            continue
        cache_key = (rel.name, token)
        if cache_key in cache:  # reuse within a turn (§31)
            cached = cache[cache_key]
            if cached[0]:
                return cached
            continue
        value, provenance = await rel.resolver(db, school_id, token)
        cache[cache_key] = (value, provenance)
        if value:
            return value, provenance
    return None, None


async def derive_parameters(
    db: AsyncSession,
    school_id: uuid.UUID,
    decision: Any,
    prev_state: Any,
    *,
    trace: dict[str, Any] | None = None,
) -> None:
    """Fill missing REQUIRED+derivable params for the chosen capability via the registry.

    Runs after conversational merge, before execution. Mutates decision.params; records
    provenance + derivation path in trace. Generic: no per-capability or per-relationship
    branch (§9). Never overrides an explicit/inherited value (§19/§26).
    """
    if getattr(decision, "action", None) != "tool":
        return
    contract = get_contract(getattr(decision, "tool", None))
    if contract is None:
        return

    params = dict(getattr(decision, "params", {}) or {})
    known = _known_entities(params, prev_state)
    provenance: list[dict[str, Any]] = []
    cache: dict[tuple[str, str], tuple[str | None, dict | None]] = {}

    for p in contract.params.values():
        if not p.derive_from or SRC_DERIVED not in p.sources:
            continue
        if params.get(p.name):
            continue  # EXPLICIT/INHERITED already present — never override (§19/§26)
        value, derived_from = await _derive_one(
            db, school_id, p.type, p.derive_from, known, cache=cache
        )
        if value:
            params[p.name] = value
            provenance.append({
                "parameter": p.name, "value": value,
                "source": SRC_DERIVED, "derived_from": derived_from,
            })

    decision.params = params
    if trace is not None and provenance:
        trace["param_provenance"] = provenance
        trace["derivation_path"] = [
            f"{pr['derived_from']['entity_type']} "
            f"-{pr['derived_from']['relationship']}-> {pr['derived_from']['to']}={pr['value']}"
            for pr in provenance if pr.get("derived_from")
        ]
