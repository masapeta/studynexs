"""Machine-readable capability contracts + canonical relationship registry (P1.5).

Prose tool descriptions told the LLM *how* to use a capability but gave neither the planner
nor the derivation engine a structured view of REQUIRED PARAMETERS, their allowed SOURCES, or
the RELATIONSHIPS that can derive them. That is why "who teaches the class ARM0242 is in?"
failed: the planner couldn't see that ``teachers_for_class`` needs a class and that a class is
derivable from a student. This module makes that knowledge structured and shared:

  Capability Contract Registry  — per-capability {entity, operation, scope, temporal_mode,
                                  params{name,type,required,sources,derive_from}}.
  Relationship Registry         — canonical relationships (student -belongs_to-> class) with a
                                  resolver/adapter; the semantic edge, NOT the physical column.

Both are validated fail-fast (at import / test time) so a dangling contract or relationship is
caught before any production query. This is metadata over the EXISTING services — no graph DB,
no second capability system, no physical schema in the LLM-facing layer.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

# Parameter sources / provenance (shared with the derivation engine).
SRC_EXPLICIT = "EXPLICIT"
SRC_INHERITED = "INHERITED"
SRC_DERIVED = "DERIVED"
SRC_DEFAULT = "SAFE_DEFAULT"
SRC_UNAVAILABLE = "UNAVAILABLE"
_VALID_SOURCES = frozenset({SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED, SRC_DEFAULT})

# Canonical semantic entity types (school-agnostic; physical mapping lives in adapters).
_VALID_ENTITIES = frozenset(
    {"student", "class", "subject", "teacher", "fee", "attendance", "exam_result",
     "staff", "school"}
)
_VALID_TEMPORAL = frozenset({"event_time", "current_state", "timeless"})
_VALID_SCOPE = frozenset({"student", "class", "school", "none"})


@dataclass(frozen=True)
class ParamContract:
    """One capability parameter: its canonical type + where its value may come from."""

    name: str
    type: str                       # canonical entity type or a scalar: number/time/string
    required: bool = False
    sources: tuple[str, ...] = (SRC_EXPLICIT, SRC_INHERITED)
    # Entity types this param can be DERIVED from via the relationship registry (e.g. a
    # "class" param derivable from a "student" the user named). Empty = not derivable.
    derive_from: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityContract:
    """Semantic contract for a capability, separate from its execution adapter (the tool)."""

    name: str
    entity: str                     # primary semantic entity/domain the capability serves
    operation: str                  # lookup / list / rank / aggregate / filter …
    scope: str                      # student / class / school / none (authorization shape)
    temporal_mode: str              # mirrors the tool's temporal_mode (validated equal)
    params: dict[str, ParamContract] = field(default_factory=dict)

    @property
    def required_params(self) -> list[str]:
        return [p.name for p in self.params.values() if p.required]

    def derivable_params(self) -> list[ParamContract]:
        return [p for p in self.params.values() if p.derive_from]


# ── Relationship registry ──────────────────────────────────────────────────────
# A resolver takes (db, school_id, source_value) and returns (target_value, detail) or
# (None, None) when missing/ambiguous (deterministic — never a guess).
RelationshipResolver = Callable[
    [AsyncSession, uuid.UUID, str], Awaitable[tuple[str | None, dict[str, Any] | None]]
]


@dataclass(frozen=True)
class Relationship:
    """A canonical semantic edge (not a physical FK): source -name-> target."""

    name: str                       # belongs_to / assigned_to …
    source: str                     # source entity type
    target: str                     # target entity type
    cardinality: str                # many_to_one / one_to_many / many_to_many
    temporal_mode: str              # current_state / event_time
    resolver: RelationshipResolver  # authoritative adapter (SQL under the hood)
    # The param name a resolved target fills when used for derivation (e.g. class -> class_label).
    target_param: str = ""


_VALID_CARDINALITY = frozenset({"many_to_one", "one_to_many", "many_to_many"})


async def _resolve_student_to_class(
    db: AsyncSession, school_id: uuid.UUID, student_token: str
) -> tuple[str | None, dict[str, Any] | None]:
    """student -belongs_to-> class: authoritative, deterministic (ambiguous/missing -> none).

    Reuses resolve_student, whose ResolvedEntity already carries the class label from the
    Student->Class join. The physical ``student.class_id`` lives here in the adapter, never in
    the semantic registry (§22).
    """
    from app.modules.workspace.assistant.resolver import resolve_student

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


# Canonical relationships verified against the real schema. Only edges the ERP actually
# represents are registered (§6). Add here — the derivation engine stays generic.
RELATIONSHIPS: tuple[Relationship, ...] = (
    Relationship(
        name="belongs_to", source="student", target="class",
        cardinality="many_to_one", temporal_mode="current_state",
        resolver=_resolve_student_to_class, target_param="class_label",
    ),
)


def find_relationship(source: str, target: str) -> Relationship | None:
    for r in RELATIONSHIPS:
        if r.source == source and r.target == target:
            return r
    return None


# ── Capability contract registry ───────────────────────────────────────────────
# One contract per governed capability. ``type`` uses canonical entity types so derivation
# and the planner reason semantically; scalar params use number/time/string.
_C = CapabilityContract
_P = ParamContract

CAPABILITY_CONTRACTS: dict[str, CapabilityContract] = {
    "school_overview": _C("school_overview", "school", "aggregate", "school", "timeless"),
    "fee_collection": _C("fee_collection", "fee", "aggregate", "school", "timeless"),
    "fee_collection_period": _C(
        "fee_collection_period", "fee", "aggregate", "school", "event_time",
        params={"time": _P("time", "time")},
    ),
    "students_fee_pending_over": _C(
        "students_fee_pending_over", "fee", "filter", "school", "timeless",
        params={
            "min_percent": _P("min_percent", "number"),
            "class_label": _P("class_label", "class", sources=(SRC_EXPLICIT, SRC_INHERITED,
                                                               SRC_DERIVED),
                              derive_from=("student",)),
        },
    ),
    "staff_directory": _C(
        "staff_directory", "staff", "list", "school", "timeless",
        params={"department": _P("department", "string")},
    ),
    "teachers_for_class": _C(
        "teachers_for_class", "teacher", "list", "class", "current_state",
        params={
            "class_label": _P("class_label", "class",
                              sources=(SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED),
                              derive_from=("student",)),
            "time": _P("time", "time"),
        },
    ),
    "teacher_assignments": _C(
        "teacher_assignments", "teacher", "lookup", "school", "current_state",
        params={"teacher": _P("teacher", "teacher", required=True), "time": _P("time", "time")},
    ),
    "student_attendance": _C(
        "student_attendance", "attendance", "aggregate", "student", "event_time",
        params={"student": _P("student", "student", required=True), "time": _P("time", "time")},
    ),
    "student_profile": _C(
        "student_profile", "student", "lookup", "student", "current_state",
        params={"student": _P("student", "student", required=True), "time": _P("time", "time")},
    ),
    "student_fees": _C(
        "student_fees", "fee", "lookup", "student", "timeless",
        params={"student": _P("student", "student", required=True)},
    ),
    "student_marks": _C(
        "student_marks", "exam_result", "lookup", "student", "timeless",
        params={
            "student": _P("student", "student", required=True),
            "subject": _P("subject", "subject"),
        },
    ),
    "class_roster": _C(
        "class_roster", "student", "list", "class", "current_state",
        params={
            "class_label": _P("class_label", "class", required=True,
                              sources=(SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED),
                              derive_from=("student",)),
            "time": _P("time", "time"),
        },
    ),
    "class_attendance_today": _C(
        "class_attendance_today", "attendance", "aggregate", "class", "timeless",
        params={
            "class_label": _P("class_label", "class", required=True,
                              sources=(SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED),
                              derive_from=("student",)),
        },
    ),
    "low_attendance_students": _C(
        "low_attendance_students", "attendance", "filter", "class", "timeless",
        params={
            "below_percent": _P("below_percent", "number"),
            "class_label": _P("class_label", "class",
                              sources=(SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED),
                              derive_from=("student",)),
        },
    ),
    "class_results": _C(
        "class_results", "exam_result", "rank", "class", "timeless",
        params={
            "class_label": _P("class_label", "class", required=True,
                              sources=(SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED),
                              derive_from=("student",)),
            "top": _P("top", "number"), "bottom": _P("bottom", "number"),
        },
    ),
    "subject_toppers": _C(
        "subject_toppers", "exam_result", "rank", "class", "timeless",
        params={
            "class_label": _P("class_label", "class", required=True,
                              sources=(SRC_EXPLICIT, SRC_INHERITED, SRC_DERIVED),
                              derive_from=("student",)),
            "subject": _P("subject", "subject", required=True),
            "top": _P("top", "number"), "bottom": _P("bottom", "number"),
        },
    ),
}


def get_contract(name: str | None) -> CapabilityContract | None:
    return CAPABILITY_CONTRACTS.get(name or "")


# ── Derived semantic views (contract = single source of truth) ──────────────────
# Consumers (conversation carry-over, composition, planner) read these instead of keeping
# their own parallel maps. One definition (the contract) -> many consumers.

# Canonical entity type -> the coarser conversational DOMAIN grouping. This is the ONLY place
# the grouping lives; it is deliberately coarser than `entity` (exam_result -> "exams",
# school -> "overview") because a follow-up "domain" spans several entities of a topic.
_ENTITY_DOMAIN: dict[str, str] = {
    "attendance": "attendance",
    "fee": "fees",
    "exam_result": "exams",
    "student": "students",
    "teacher": "teachers",
    "staff": "staff",
    "school": "overview",
}

# An entity-typed param may be addressed by more than one param key in practice (a resolver
# may fill `student` or `student_id`). This alias table is the single place that mapping lives.
ENTITY_PARAM_ALIASES: dict[str, frozenset[str]] = {
    "student": frozenset({"student", "student_id"}),
    "class": frozenset({"class_label", "class"}),
    "teacher": frozenset({"teacher", "teacher_id"}),
}


def domain_for_entity(entity: str | None) -> str | None:
    """The conversational domain a capability belongs to, derived from its contract entity."""
    return _ENTITY_DOMAIN.get(entity or "")


def domain_for_capability(name: str | None) -> str | None:
    """The conversational domain of a capability, via its contract (no per-capability map)."""
    c = get_contract(name)
    return domain_for_entity(c.entity) if c else None


def entity_param_keys(contract: CapabilityContract | None) -> frozenset[str]:
    """Param keys that identify the 'who/what' of a capability, derived from its contract.

    Expands each entity-typed param (student/class/teacher) to its accepted key aliases, so
    conversational carry-over never injects an entity into a capability that doesn't take one.
    """
    if contract is None:
        return frozenset()
    keys: set[str] = set()
    for p in contract.params.values():
        alias = ENTITY_PARAM_ALIASES.get(p.type)
        if alias:
            keys |= alias
    return frozenset(keys)


def is_current_state(name: str | None) -> bool:
    """Whether a governed capability reflects only the present state (no history), from contract."""
    c = get_contract(name)
    return bool(c and c.temporal_mode == "current_state")


# ── Fail-fast validation (§16, §17) ────────────────────────────────────────────


class ContractError(Exception):
    """Raised when a capability contract or relationship is structurally invalid."""


def validate_registries() -> None:
    """Validate contracts + relationships and detect SEMANTIC DRIFT against the tool catalog.

    The contract is the single semantic source of truth; the tool catalog is its runtime
    adapter (handler + planner-facing prose). This checks the two never diverge silently:
      - every contract maps to a real tool AND every tool has a contract (no orphans);
      - tool param KEYS == contract param names (a param added to one but not the other);
      - the contract entity has a conversational domain (so carry-over can derive it);
      - scope/temporal/source/derive metadata is structurally valid.
    (temporal_mode is no longer duplicated on the tool — it is a property reading the contract,
    so an equality check would be tautological; drift is prevented at the source instead.)
    Called at import time and in tests so bad metadata fails before a production query.
    """
    from app.modules.workspace.assistant.tools import ASSISTANT_TOOLS

    tool_by_name = {t.name: t for t in ASSISTANT_TOOLS}

    # Every runtime tool must have a semantic contract (drift: a capability with no source).
    for tname in tool_by_name:
        if tname not in CAPABILITY_CONTRACTS:
            raise ContractError(f"tool '{tname}' has no capability contract")

    for name, c in CAPABILITY_CONTRACTS.items():
        if c.name != name:
            raise ContractError(f"contract key '{name}' != contract.name '{c.name}'")
        if c.entity not in _VALID_ENTITIES:
            raise ContractError(f"{name}: unknown entity '{c.entity}'")
        if c.temporal_mode not in _VALID_TEMPORAL:
            raise ContractError(f"{name}: bad temporal_mode '{c.temporal_mode}'")
        if c.scope not in _VALID_SCOPE:
            raise ContractError(f"{name}: bad scope '{c.scope}'")
        if domain_for_entity(c.entity) is None:
            raise ContractError(f"{name}: entity '{c.entity}' has no conversational domain")
        tool = tool_by_name.get(name)
        if tool is None:
            raise ContractError(f"contract '{name}' has no matching tool")
        # Param-key drift: the planner-facing tool params and the contract params must agree.
        tool_param_keys = set(tool.params)
        contract_param_keys = set(c.params)
        if tool_param_keys != contract_param_keys:
            raise ContractError(
                f"{name}: tool params {sorted(tool_param_keys)} != contract params "
                f"{sorted(contract_param_keys)}"
            )
        for pname, p in c.params.items():
            if p.name != pname:
                raise ContractError(f"{name}: param key '{pname}' != '{p.name}'")
            for s in p.sources:
                if s not in _VALID_SOURCES:
                    raise ContractError(f"{name}.{pname}: bad source '{s}'")
            if p.derive_from and SRC_DERIVED not in p.sources:
                raise ContractError(
                    f"{name}.{pname}: derive_from set but DERIVED not in sources"
                )
            for src_entity in p.derive_from:
                if src_entity not in _VALID_ENTITIES:
                    raise ContractError(f"{name}.{pname}: unknown derive_from '{src_entity}'")
                # A path must exist from the source entity to this param's entity type.
                if not find_relationship(src_entity, p.type):
                    raise ContractError(
                        f"{name}.{pname}: no relationship {src_entity} -> {p.type}"
                    )

    for r in RELATIONSHIPS:
        if r.source not in _VALID_ENTITIES or r.target not in _VALID_ENTITIES:
            raise ContractError(f"relationship '{r.name}': unknown entity")
        if r.cardinality not in _VALID_CARDINALITY:
            raise ContractError(f"relationship '{r.name}': bad cardinality")
        if r.temporal_mode not in _VALID_TEMPORAL:
            raise ContractError(f"relationship '{r.name}': bad temporal_mode")
        if not callable(r.resolver):
            raise ContractError(f"relationship '{r.name}': resolver not callable")
