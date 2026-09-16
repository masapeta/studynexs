"""Historical-honesty guard (Phase 5 / P0).

A PAST request on a current-state relationship capability must be blocked BEFORE the
current-state query runs — never silently answered with present data (spec §6, §15).
Transactional (event_time) capabilities and current requests must still work.
"""


import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School
from app.modules.workspace.assistant.temporal import resolve_time_range
from app.modules.workspace.assistant.tools import get_tool

# ── Temporal classification: PAST vs CURRENT vs event ─────────────────────────


@pytest.mark.asyncio
async def test_temporality_classification(test_school: School, db_session: AsyncSession):
    today = await resolve_time_range(db_session, test_school, test_school.id, "today")
    assert today.temporality == "CURRENT"
    assert not today.is_past

    this_month = await resolve_time_range(db_session, test_school, test_school.id, "this_month")
    assert this_month.temporality == "CURRENT"

    last_month = await resolve_time_range(db_session, test_school, test_school.id, "last_month")
    assert last_month.temporality == "PAST"
    assert last_month.is_past

    last_year = await resolve_time_range(db_session, test_school, test_school.id, "last_year")
    assert last_year.temporality == "PAST"

    all_time = await resolve_time_range(db_session, test_school, test_school.id, "all_time")
    assert all_time.temporality == "UNSPECIFIED"
    assert not all_time.is_past  # never blocks

    # A past explicit month resolves to PAST; a future one to FUTURE.
    past = await resolve_time_range(
        db_session, test_school, test_school.id, {"from": "2024-01-01", "to": "2024-01-31"}
    )
    assert past.temporality == "PAST"


# ── Capability contract ───────────────────────────────────────────────────────


def test_capability_temporal_contract():
    # current-state relationships cannot answer history
    assert get_tool("teachers_for_class").temporal_mode == "current_state"
    assert get_tool("teachers_for_class").supports_historical is False
    assert get_tool("student_profile").supports_historical is False
    assert get_tool("class_roster").supports_historical is False
    # event-time transactional capabilities support past ranges
    assert get_tool("student_attendance").supports_historical is True
    assert get_tool("fee_collection_period").supports_historical is True


# ── Service guard: PAST + current_state is blocked BEFORE the handler runs ─────


class _FakeUser:
    def __init__(self, school_id, role="super_admin"):
        self.school_id = str(school_id)
        self.role = role
        self.id = str(school_id)


@pytest.mark.asyncio
async def test_guard_blocks_historical_relationship_without_executing(
    test_school: School, db_session: AsyncSession
):
    """PAST + current_state -> historical block, and the handler is proven NOT to run.

    We pass a class label that does NOT exist. If the handler executed, it would return a
    'class not found' block; the guard instead returns the historical-unavailable block
    BEFORE the handler — so the distinct title proves the current-state query never ran.
    """
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    trace: dict = {}
    block = await svc._run_tool(
        user, "teachers_for_class",
        {"class_label": "does-not-exist-Z9", "time": "last_month"}, test_school.id, trace=trace,
    )
    assert block["kind"] == "not_found"
    assert block["title"] == "Historical records not available"  # NOT the handler's output
    # Trace proves the guard decision fired before execution.
    assert trace["historical_guard"]["decision"] == "blocked"
    assert trace["historical_guard"]["capability"] == "teachers_for_class"
    assert trace["time_range"]["temporality"] == "PAST"


@pytest.mark.asyncio
async def test_guard_allows_current_relationship(
    test_school: School, test_class, db_session: AsyncSession
):
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    # No time / current time -> executes normally (returns a table, not a block).
    block = await svc._run_tool(
        user, "teachers_for_class", {"class_label": "Grade 1 A"}, test_school.id, trace={}
    )
    assert block["kind"] == "table"


@pytest.mark.asyncio
async def test_guard_allows_historical_transactional(
    test_school: School, admin_user, db_session: AsyncSession
):
    """event_time capability (fees) must still answer a PAST range — not blocked."""
    from app.modules.workspace.assistant.service import AssistantService

    svc = AssistantService(db_session)
    user = _FakeUser(test_school.id)
    block = await svc._run_tool(
        user, "fee_collection_period", {"time": {"from": "2024-08-01", "to": "2024-08-31"}},
        test_school.id, trace={},
    )
    # metrics (a real, if zero, collection) — NOT a historical-unavailable block.
    assert block["kind"] == "metrics"
    assert "Historical" not in block.get("title", "")


# ── Composition guard (§11) ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_composition_blocks_historical_current_state(
    test_school: School, db_session: AsyncSession
):
    from app.modules.workspace.assistant.composition import (
        CompositionError,
        execute_plan,
        parse_plan,
    )

    async def past_range(_sid, _tok):
        return await resolve_time_range(db_session, test_school, test_school.id, "last_year")

    plan = parse_plan({
        "operations": [
            {"id": "c", "capability": "classes_overview", "params": {"time": "last_year"}},
        ]
    })

    class _U:
        school_id = str(test_school.id)
        role = "super_admin"
        id = str(test_school.id)

    with pytest.raises(CompositionError):
        await execute_plan(db_session, _U(), plan, resolve_range=past_range)
