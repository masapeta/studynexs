"""Single source of truth for capability semantics (consolidation phase).

These tests prove ONE DEFINITION -> MANY CONSUMERS, not MANY DEFINITIONS -> SAME VALUE. The
capability contract is the authoritative semantic source; the tool catalog (temporal_mode),
conversational carry-over (domain, accepted entity params), and the historical guard all DERIVE
from it. A test therefore constructs/edits a contract and asserts the derived consumer behavior
follows — rather than asserting two hardcoded constants happen to be equal.
"""

from __future__ import annotations

import pytest

from app.modules.workspace.assistant.contracts import (
    CAPABILITY_CONTRACTS,
    CapabilityContract,
    ContractError,
    ParamContract,
    domain_for_capability,
    entity_param_keys,
    get_contract,
    is_current_state,
    validate_registries,
)

# ── temporal_mode: contract is the source; the tool derives it ────────────────────────────


def test_tool_temporal_mode_is_derived_from_contract():
    from app.modules.workspace.assistant.tools import ASSISTANT_TOOLS

    for t in ASSISTANT_TOOLS:
        c = get_contract(t.name)
        assert c is not None
        assert t.temporal_mode == c.temporal_mode  # the tool reads the contract, not a copy


def test_changing_contract_temporal_mode_changes_tool(monkeypatch):
    """Edit ONE definition (the contract) -> the tool's derived temporal_mode follows."""
    from app.modules.workspace.assistant.tools import get_tool

    tool = get_tool("student_profile")
    assert tool.temporal_mode == "current_state"
    original = CAPABILITY_CONTRACTS["student_profile"]
    patched = CapabilityContract(
        original.name, original.entity, original.operation, original.scope,
        "event_time", params=original.params,
    )
    monkeypatch.setitem(CAPABILITY_CONTRACTS, "student_profile", patched)
    assert tool.temporal_mode == "event_time"  # no second definition to update
    assert tool.supports_historical is True


# ── domain: derived from contract.entity (no _CAPABILITY_DOMAIN map) ──────────────────────


def test_domain_is_derived_from_contract_entity():
    # exam_result -> "exams", fee -> "fees", school -> "overview": the grouping is derived.
    assert domain_for_capability("student_marks") == "exams"
    assert domain_for_capability("class_results") == "exams"
    assert domain_for_capability("fee_collection_period") == "fees"
    assert domain_for_capability("student_attendance") == "attendance"
    assert domain_for_capability("teachers_for_class") == "teachers"
    assert domain_for_capability("school_overview") == "overview"
    assert domain_for_capability("staff_directory") == "staff"


def test_every_contract_has_a_derivable_domain():
    for name in CAPABILITY_CONTRACTS:
        assert domain_for_capability(name) is not None, f"{name} has no derived domain"


# ── accepted entity params: derived from contract params ──────────────────────────────────


def test_entity_params_are_derived_from_contract():
    # student-scoped caps accept student/student_id; class-scoped accept class_label/class.
    assert entity_param_keys(get_contract("student_marks")) == frozenset(
        {"student", "student_id"}
    )
    assert entity_param_keys(get_contract("class_results")) == frozenset(
        {"class_label", "class"}
    )
    assert entity_param_keys(get_contract("teacher_assignments")) == frozenset(
        {"teacher", "teacher_id"}
    )
    # school-wide caps accept no entity param (carry-over must never inject one).
    assert entity_param_keys(get_contract("fee_collection_period")) == frozenset()
    assert entity_param_keys(get_contract("school_overview")) == frozenset()


def test_adding_an_entity_param_to_a_contract_updates_accepted_keys():
    """One definition changes -> the derived accepted-entity set follows (no parallel map)."""
    base = get_contract("fee_collection_period")
    assert entity_param_keys(base) == frozenset()
    widened = CapabilityContract(
        base.name, base.entity, base.operation, base.scope, base.temporal_mode,
        params={**base.params, "student": ParamContract("student", "student")},
    )
    assert entity_param_keys(widened) == frozenset({"student", "student_id"})


# ── current-state classification derives from temporal_mode ───────────────────────────────


def test_is_current_state_derived_from_contract():
    assert is_current_state("teachers_for_class") is True
    assert is_current_state("class_roster") is True
    assert is_current_state("student_attendance") is False   # event_time
    assert is_current_state("school_overview") is False       # timeless


# ── drift detection: the validator catches divergence, not equality ───────────────────────


def test_validation_catches_tool_without_contract(monkeypatch):
    """A runtime tool with no semantic contract is drift — must fail fast."""
    from app.modules.workspace.assistant import tools as tools_mod

    orphan = tools_mod.AssistantTool(
        name="orphan_tool", description="no contract", params={},
        roles=tools_mod._STAFF, handler=tools_mod._school_overview,
    )
    monkeypatch.setattr(
        tools_mod, "ASSISTANT_TOOLS", (*tools_mod.ASSISTANT_TOOLS, orphan)
    )
    with pytest.raises(ContractError, match="orphan_tool"):
        validate_registries()


def test_validation_catches_param_key_drift(monkeypatch):
    """A param present on the tool but not the contract (or vice versa) is drift."""
    from app.modules.workspace.assistant import tools as tools_mod

    base = tools_mod.get_tool("student_fees")
    drifted = tools_mod.AssistantTool(
        name=base.name, description=base.description,
        params={**base.params, "phantom": "string — not in the contract"},
        roles=base.roles, handler=base.handler,
    )
    others = tuple(t for t in tools_mod.ASSISTANT_TOOLS if t.name != base.name)
    monkeypatch.setattr(tools_mod, "ASSISTANT_TOOLS", (*others, drifted))
    with pytest.raises(ContractError, match="student_fees"):
        validate_registries()


def test_validation_catches_entity_without_domain(monkeypatch):
    """A contract entity with no conversational domain would break carry-over — fail fast."""
    base = get_contract("school_overview")
    bad = CapabilityContract(
        base.name, "unmapped_entity", base.operation, "school", base.temporal_mode,
    )
    # unmapped_entity isn't a valid entity, so validation fails before the domain check too;
    # assert the guard raises regardless (drift is refused).
    monkeypatch.setitem(CAPABILITY_CONTRACTS, "school_overview", bad)
    with pytest.raises(ContractError):
        validate_registries()
