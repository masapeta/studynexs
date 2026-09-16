"""Temporal-integrity hardening (Phase 5 / P0.1).

The P0 guard only fired when the planner attached the historical time to the tool's
params. This phase closes the real vulnerability: a planner that understands the request
is PAST but DROPS ``params.time`` while selecting a current-state tool must NOT be allowed
to silently answer with current data. Temporal meaning is carried as a SEPARATE semantic
signal and compared against the plan's temporality; a drop is detected and blocked.

These tests exercise planner degradation directly (semantic=PAST, params has no time) —
not just a manually-constructed historical range — which is what proves the fix.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School
from app.modules.workspace.assistant.temporal import (
    INTEGRITY_ALLOW,
    INTEGRITY_BLOCK_UNSUPPORTED,
    INTEGRITY_DROPPED,
    resolve_time_range,
    semantic_temporality,
    temporal_integrity,
)


class _FakeUser:
    def __init__(self, school_id, role="super_admin", user_id=None):
        self.school_id = str(school_id)
        self.role = role
        self.id = str(user_id or school_id)
        self.full_name = "Test Admin"


# ── Pure integrity function (no keywords, structured only) ────────────────────


def test_temporal_integrity_matrix():
    # PAST semantic + current-state capability -> BLOCK_UNSUPPORTED regardless of plan
    # (relationship history is never kept; the capability simply can't answer the past).
    assert (
        temporal_integrity(semantic="PAST", plan="NONE", supports_historical=False)
        == INTEGRITY_BLOCK_UNSUPPORTED
    )
    assert (
        temporal_integrity(semantic="PAST", plan="PAST", supports_historical=False)
        == INTEGRITY_BLOCK_UNSUPPORTED
    )
    # PAST semantic + event-time capability + plan PAST -> ALLOW (window applied).
    assert (
        temporal_integrity(semantic="PAST", plan="PAST", supports_historical=True)
        == INTEGRITY_ALLOW
    )
    # PAST + event-time + plan not PAST + CONCRETE window -> the window was dropped -> DROPPED.
    assert (
        temporal_integrity(
            semantic="PAST", plan="NONE", supports_historical=True, semantic_concrete=True
        )
        == INTEGRITY_DROPPED
    )
    # PAST + event-time + plan not PAST + NO concrete window -> all-time question -> ALLOW.
    assert (
        temporal_integrity(
            semantic="PAST", plan="NONE", supports_historical=True, semantic_concrete=False
        )
        == INTEGRITY_ALLOW
    )
    # CURRENT semantic + current-state -> ALLOW (the normal case).
    assert (
        temporal_integrity(semantic="CURRENT", plan="NONE", supports_historical=False)
        == INTEGRITY_ALLOW
    )
    # NONE semantic -> ALLOW (no temporal expectation).
    assert (
        temporal_integrity(semantic="NONE", plan="NONE", supports_historical=False)
        == INTEGRITY_ALLOW
    )


@pytest.mark.asyncio
async def test_semantic_temporality_prefers_resolved_dates(
    test_school: School, db_session: AsyncSession
):
    # Declared PAST with a resolvable past window -> PAST from the dates.
    rng = await resolve_time_range(
        db_session, test_school, test_school.id, {"from": "2024-01-01", "to": "2024-01-31"}
    )
    assert semantic_temporality("PAST", rng) == "PAST"
    # Declared PAST but no resolvable window -> still PAST (safe assumption).
    assert semantic_temporality("PAST", None) == "PAST"
    # Declared PERIOD without a window -> PAST (forces the integrity check).
    assert semantic_temporality("PERIOD", None) == "PAST"
    # Declared NONE -> NONE.
    assert semantic_temporality("NONE", None) == "NONE"


# ── THE REAL BUG: planner drops the time on a current-state tool ──────────────


@pytest.mark.asyncio
async def test_dropped_qualifier_is_blocked_without_executing(
    test_school: School, db_session: AsyncSession
):
    """semantic=PAST but params has NO time (planner dropped it) -> blocked, handler not run.

    A current-state relationship capability can never answer the past, so the reason is
    BLOCK_UNSUPPORTED. Uses a non-existent class: if the handler ran it would return 'class
    not found'. The integrity guard instead returns the historical-unavailable block BEFORE
    the handler, proving the current-state query never executed.
    """
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    trace: dict = {}
    block = await svc._run_tool(
        user,
        "teachers_for_class",
        {"class_label": "does-not-exist-Z9"},  # NOTE: no 'time' — the drop we defend against
        test_school.id,
        trace=trace,
        semantic="PAST",  # the semantic layer still knows it was historical
        semantic_label="last year",
    )
    assert block["kind"] == "not_found"
    assert block["title"] == "Historical records not available"  # NOT 'class not found'
    assert trace["temporal_integrity"] == "FAILED"
    assert trace["temporal_guard_decision"] == INTEGRITY_BLOCK_UNSUPPORTED
    assert trace["historical_guard"]["decision"] == "blocked"
    assert trace["plan_temporality"] == "NONE"


@pytest.mark.asyncio
async def test_dropped_qualifier_student_class_blocked(
    test_school: School, db_session: AsyncSession
):
    """'which class was ARM0218 last year' with time dropped -> blocked, profile not run."""
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    trace: dict = {}
    block = await svc._run_tool(
        user,
        "student_profile",
        {"student": "does-not-exist-ADM"},  # no time; handler would say 'not found'
        test_school.id,
        trace=trace,
        semantic="PAST",
        semantic_label="last year",
    )
    assert block["kind"] == "not_found"
    assert block["title"] == "Historical records not available"
    assert trace["temporal_guard_decision"] == INTEGRITY_BLOCK_UNSUPPORTED


# ── Current + transactional still work through the integrity path ─────────────


@pytest.mark.asyncio
async def test_current_relationship_still_allowed(
    test_school: School, test_class, db_session: AsyncSession
):
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    block = await svc._run_tool(
        user, "teachers_for_class", {"class_label": "Grade 1 A"}, test_school.id,
        trace={}, semantic="CURRENT",
    )
    assert block["kind"] == "table"  # executed normally


@pytest.mark.asyncio
async def test_historical_transactional_still_allowed(
    test_school: School, admin_user, db_session: AsyncSession
):
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    trace: dict = {}
    block = await svc._run_tool(
        user, "fee_collection_period", {"time": {"from": "2024-08-01", "to": "2024-08-31"}},
        test_school.id, trace=trace, semantic="PAST", semantic_label="August 2024",
    )
    assert block["kind"] == "metrics"  # event-time supports history
    assert trace["temporal_guard_decision"] == INTEGRITY_ALLOW


# ── End-to-end handle_turn with a DEGRADED planner (spec §15, §16) ────────────


@pytest.mark.asyncio
async def test_handle_turn_degraded_planner_blocks(
    test_school: School, admin_user, db_session: AsyncSession, monkeypatch
):
    """Full pipeline: planner understands PAST but drops params.time -> blocked, not answered.

    This simulates the exact LLM degradation the phase defends against: the temporal object
    says PAST while the chosen current-state tool has no time. handle_turn must block and
    record the integrity failure in the trace.
    """
    from app.modules.workspace.assistant import service as service_mod
    from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent

    async def _degraded_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(
            route="STRUCTURED",
            action="tool",
            tool="teachers_for_class",
            params={"class_label": "does-not-exist-Z9"},  # time DROPPED here
            temporal=TemporalIntent(presence="PAST", time="last_year"),  # but semantics say PAST
        )

    monkeypatch.setattr(service_mod, "plan", _degraded_plan)

    svc = service_mod.AssistantService(db_session)
    user = _FakeUser(test_school.id, user_id=admin_user.id)
    result = await svc.handle_turn(current_user=user, text="who was the teacher of 2A last year?", session_id=None)

    assert result["block"]["title"] == "Historical records not available"
    tr = result["trace"]
    assert tr["semantic_temporality"] == "PAST"
    assert tr["plan_temporality"] == "NONE"
    assert tr["temporal_integrity"] == "FAILED"
    # current-state capability can never answer the past -> BLOCK_UNSUPPORTED (still blocked).
    assert tr["temporal_guard_decision"] == INTEGRITY_BLOCK_UNSUPPORTED


@pytest.mark.asyncio
async def test_handle_turn_event_time_dropped_window(
    test_school: School, admin_user, db_session: AsyncSession, monkeypatch
):
    """event-time tool + CONCRETE past window that the plan dropped -> TEMPORAL_CONSTRAINT_DROPPED.

    'fee collected in August' understood as PAST(August) but params.time dropped: we must
    refuse (not answer all-time), because a concrete window was lost.
    """
    from app.modules.workspace.assistant import service as service_mod
    from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent

    async def _degraded_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(
            route="STRUCTURED",
            action="tool",
            tool="fee_collection_period",
            params={},  # concrete window dropped
            temporal=TemporalIntent(presence="PAST", time={"month": "august"}),
        )

    monkeypatch.setattr(service_mod, "plan", _degraded_plan)
    svc = service_mod.AssistantService(db_session)
    user = _FakeUser(test_school.id, user_id=admin_user.id)
    result = await svc.handle_turn(
        current_user=user, text="how much did we collect in August?", session_id=None
    )
    tr = result["trace"]
    assert tr["semantic_temporality"] == "PAST"
    assert tr["temporal_integrity"] == "FAILED"
    assert tr["temporal_guard_decision"] == INTEGRITY_DROPPED


@pytest.mark.asyncio
async def test_handle_turn_event_time_all_time_allowed(
    test_school: School, admin_user, db_session: AsyncSession, monkeypatch
):
    """event-time tool + weak/ongoing PAST (no concrete window) -> ALLOW (all-time answer).

    'how often has X been attending' is present-perfect -> may be tagged PAST, but it's an
    all-time question; it must NOT be mistaken for a dropped historical window.
    """
    from app.modules.workspace.assistant import service as service_mod
    from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent

    async def _plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(
            route="STRUCTURED",
            action="tool",
            tool="student_attendance",
            params={"student": "does-not-exist-ADM", "time": "all_time"},
            temporal=TemporalIntent(presence="PAST", time="all_time"),
        )

    monkeypatch.setattr(service_mod, "plan", _plan)
    svc = service_mod.AssistantService(db_session)
    user = _FakeUser(test_school.id, user_id=admin_user.id)
    result = await svc.handle_turn(
        current_user=user, text="how often has ADM been coming?", session_id=None
    )
    tr = result["trace"]
    assert tr["temporal_integrity"] == "OK"
    assert tr["temporal_guard_decision"] == INTEGRITY_ALLOW
    # handler ran -> honest not_found for the unknown student (NOT a temporal block).
    assert result["block"]["kind"] == "not_found"


@pytest.mark.asyncio
async def test_handle_turn_current_planner_allows(
    test_school: School, test_class, admin_user, db_session: AsyncSession, monkeypatch
):
    """Current request end-to-end still executes (no false positive)."""
    from app.modules.workspace.assistant import service as service_mod
    from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent

    async def _current_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(
            route="STRUCTURED",
            action="tool",
            tool="teachers_for_class",
            params={"class_label": "Grade 1 A"},
            temporal=TemporalIntent(presence="CURRENT", time=None),
        )

    monkeypatch.setattr(service_mod, "plan", _current_plan)

    svc = service_mod.AssistantService(db_session)
    user = _FakeUser(test_school.id, user_id=admin_user.id)
    result = await svc.handle_turn(current_user=user, text="who is the teacher of 1A?", session_id=None)
    assert result["block"]["kind"] == "table"
    assert result["trace"]["temporal_integrity"] == "OK"


# ── Composition: dropped qualifier on a current-state op is caught ────────────


@pytest.mark.asyncio
async def test_composition_blocks_dropped_qualifier(
    test_school: School, db_session: AsyncSession
):
    """semantic=PAST + classes_overview with NO op time -> blocked (no silent current join)."""
    from app.modules.workspace.assistant.composition import (
        CompositionError,
        execute_plan,
        parse_plan,
    )

    async def any_range(_sid, _tok):
        return await resolve_time_range(db_session, test_school, test_school.id, _tok)

    # No 'time' in params — the qualifier was dropped, but semantic says PAST.
    plan = parse_plan({
        "operations": [{"id": "c", "capability": "classes_overview", "params": {}}]
    })
    user = _FakeUser(test_school.id)
    with pytest.raises(CompositionError):
        await execute_plan(
            db_session, user, plan, resolve_range=any_range, semantic="PAST"
        )
