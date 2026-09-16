"""Conversational semantic + temporal carry-over (P1.2).

Elliptical follow-ups ("what about September?", "his fees", "what about English?") inherit
the previous turn's unchanged dimensions and apply only what the new turn changes. Tested at
two levels:
  - the deterministic merge (merge_follow_up) in isolation — the backstop that guarantees
    precedence (§10) and the P0.1 temporal invariant (§12) regardless of the LLM;
  - end-to-end handle_turn with a monkeypatched planner that simulates the LLM DROPPING the
    temporal on a follow-up (the exact Phase 6 failure) — proving the pipeline recovers.

No keyword handling of specific phrases (§26): the merge operates purely on structured state.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School
from app.modules.workspace.assistant.conversation import (
    ConversationSemanticState,
    merge_follow_up,
    state_from_decision,
)
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent


class _U:
    def __init__(self, school_id, user_id=None, role="super_admin"):
        self.id = str(user_id or school_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "T"


def _state(**kw) -> ConversationSemanticState:
    return ConversationSemanticState(**kw)


# ── Deterministic merge: temporal carry-over (the core gap) ───────────────────


def test_fee_period_replacement_keeps_domain_and_context():
    """T1 'fee in August' -> T2 'what about September?' keeps fees+collection, swaps time."""
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  temporal_presence="PAST", temporal_time={"month": "august"})
    # T2: planner picked the fee tool again but only supplied the new month.
    d = PlannerDecision(action="tool", tool="fee_collection_period",
                        params={"time": {"month": "september"}},
                        temporal=TemporalIntent(presence="PAST", time={"month": "september"}))
    merged, tr = merge_follow_up(prev, d)
    assert merged.tool == "fee_collection_period"
    assert merged.temporal.time == {"month": "september"}
    assert merged.temporal.presence == "PAST"


def test_follow_up_drops_time_inherits_previous_period():
    """T2 forgot the time entirely -> inherit the previous period (don't go all-time)."""
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  temporal_presence="PAST", temporal_time={"month": "august"})
    d = PlannerDecision(action="tool", tool="fee_collection_period", params={},
                        temporal=TemporalIntent(presence="NONE", time=None))
    merged, tr = merge_follow_up(prev, d)
    assert merged.temporal.presence == "PAST"
    assert merged.temporal.time == {"month": "august"}
    assert "temporal:full" in tr["inherited"]


def test_historical_followup_stays_historical():
    """T1 historical teacher of 2A -> T2 'what about September?' stays PAST (P0.1, §5)."""
    prev = _state(domain="teachers", capability="teachers_for_class", action="tool",
                  entities={"class_label": "2A"}, temporal_presence="PAST",
                  temporal_time={"month": "august"})
    # LLM proposes new month but leaves presence unstated.
    d = PlannerDecision(action="tool", tool="teachers_for_class",
                        params={"class_label": "2A", "time": {"month": "september"}},
                        temporal=TemporalIntent(presence="NONE", time={"month": "september"}))
    merged, tr = merge_follow_up(prev, d)
    assert merged.temporal.presence == "PAST"  # never silently CURRENT


def test_current_followup_stays_current_class_replaced():
    """T1 'who is the class teacher of 2A?' -> T2 'what about 2B?' current + 2B (§6)."""
    prev = _state(domain="teachers", capability="teachers_for_class", action="tool",
                  entities={"class_label": "2A"}, temporal_presence="CURRENT")
    d = PlannerDecision(action="tool", tool="teachers_for_class",
                        params={"class_label": "2B"},
                        temporal=TemporalIntent(presence="CURRENT", time=None))
    merged, tr = merge_follow_up(prev, d)
    assert merged.params["class_label"] == "2B"
    assert merged.temporal.presence == "CURRENT"


# ── Entity + domain carry-over ────────────────────────────────────────────────


def test_entity_inherited_on_domain_switch():
    """T1 'ARM0218 attendance' -> T2 'his fees' keeps entity, swaps domain (§7)."""
    prev = _state(domain="attendance", capability="student_attendance", action="tool",
                  entities={"student": "ARM0218"})
    d = PlannerDecision(action="tool", tool="student_fees", params={},
                        temporal=TemporalIntent())
    merged, tr = merge_follow_up(prev, d)
    assert merged.params.get("student") == "ARM0218"
    assert "entity:student" in tr["inherited"]


def test_metric_change_keeps_time():
    """T1 'fee collected in August' -> T2 'how many receipts?' keeps August (§8)."""
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  temporal_presence="PAST", temporal_time={"month": "august"})
    d = PlannerDecision(action="tool", tool="fee_collection_period", params={},
                        temporal=TemporalIntent(presence="NONE", time=None))
    merged, tr = merge_follow_up(prev, d)
    assert merged.temporal.time == {"month": "august"}


def test_subject_change_keeps_student():
    """T1 'ARM0218 Mathematics marks' -> T2 'what about English?' keeps student, swaps subject."""
    prev = _state(domain="exams", capability="student_marks", action="tool",
                  entities={"student": "ARM0218"}, subject="Mathematics")
    d = PlannerDecision(action="tool", tool="student_marks", params={"subject": "English"},
                        temporal=TemporalIntent())
    merged, tr = merge_follow_up(prev, d)
    assert merged.params.get("student") == "ARM0218"
    assert merged.params.get("subject") == "English"


def test_no_over_inheritance_on_class_swap():
    """T1 'students in 8A below 75%' -> T2 'what about 7A?' -> 7A + threshold, NOT 8A (§14)."""
    prev = _state(domain="attendance", capability="low_attendance_students", action="tool",
                  entities={"class_label": "8A"})
    d = PlannerDecision(action="tool", tool="low_attendance_students",
                        params={"class_label": "7A", "below_percent": 75},
                        temporal=TemporalIntent())
    merged, tr = merge_follow_up(prev, d)
    assert merged.params["class_label"] == "7A"


# ── Operation / metric carry-over (P1.2a) ─────────────────────────────────────


def test_metric_switch_recovers_capability_when_llm_drops_tool():
    """T1 'fee collected in August' -> T2 'how many receipts?' where the LLM returned a guide.

    The metric-only follow-up must recover the previous capability (fee_collection_period),
    keep the August window, and switch the metric to receipt_count — no phrase-specific rule.
    """
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  temporal_presence="PAST", temporal_time={"month": "august"},
                  operation="collection", metric="amount")
    # LLM failed to pick a tool but understood the new metric.
    d = PlannerDecision(action="clarify", tool=None, params={},
                        temporal=TemporalIntent(), metric="receipt_count")
    merged, tr = merge_follow_up(prev, d)
    assert merged.tool == "fee_collection_period"
    assert merged.action == "tool"
    assert "capability" in tr["inherited"]
    assert merged.params.get("time") == {"month": "august"}  # window inherited
    assert merged.metric == "receipt_count"                   # new metric applied
    assert merged.operation == "collection"                   # operation inherited


def test_metric_switch_when_tool_kept_inherits_operation_and_time():
    """If the LLM keeps the tool but omits operation, inherit it; keep time."""
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  temporal_presence="PAST", temporal_time={"month": "august"},
                  operation="collection", metric="amount")
    d = PlannerDecision(action="tool", tool="fee_collection_period", params={},
                        temporal=TemporalIntent(), metric="receipt_count")
    merged, tr = merge_follow_up(prev, d)
    assert merged.params.get("time") == {"month": "august"}
    assert merged.operation == "collection"
    assert merged.metric == "receipt_count"


def test_capability_not_recovered_without_metric_or_operation():
    """A bare guide with no metric/operation must NOT hijack the previous capability."""
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  operation="collection", metric="amount")
    d = PlannerDecision(action="clarify", tool=None, params={}, temporal=TemporalIntent())
    merged, tr = merge_follow_up(prev, d)
    assert merged.action == "clarify"
    assert "capability" not in tr["inherited"]


def test_capability_not_recovered_when_new_entity_named():
    """A follow-up that names a NEW entity is a fresh request, not a metric continuation."""
    prev = _state(domain="fees", capability="fee_collection_period", action="tool",
                  operation="collection", metric="amount")
    d = PlannerDecision(action="clarify", tool=None, params={"student": "ARM0242"},
                        temporal=TemporalIntent(), metric="balance")
    merged, tr = merge_follow_up(prev, d)
    assert "capability" not in tr["inherited"]


# ── Adversarial follow-ups (§23) ──────────────────────────────────────────────


def test_domain_and_time_both_change():
    """T1 'attendance in August' -> T2 'September fees' -> both change, nothing stale."""
    prev = _state(domain="attendance", capability="student_attendance", action="tool",
                  entities={"student": "ARM0218"}, temporal_presence="PAST",
                  temporal_time={"month": "august"})
    d = PlannerDecision(action="tool", tool="fee_collection_period",
                        params={"time": {"month": "september"}},
                        temporal=TemporalIntent(presence="PAST", time={"month": "september"}))
    merged, tr = merge_follow_up(prev, d)
    assert merged.tool == "fee_collection_period"
    assert merged.temporal.time == {"month": "september"}
    # entity not force-carried into a school-wide fee-period query
    assert "student" not in merged.params


def test_entity_and_domain_both_change():
    """T1 'ARM0218 attendance' -> T2 'ARM0242 fees' -> entity + domain change."""
    prev = _state(domain="attendance", capability="student_attendance", action="tool",
                  entities={"student": "ARM0218"})
    d = PlannerDecision(action="tool", tool="student_fees", params={"student": "ARM0242"},
                        temporal=TemporalIntent())
    merged, tr = merge_follow_up(prev, d)
    assert merged.params["student"] == "ARM0242"


def test_relative_time_replacement_same_entity():
    """T1 'ARM0218 attendance this month' -> T2 'last month' keeps student+attendance."""
    prev = _state(domain="attendance", capability="student_attendance", action="tool",
                  entities={"student": "ARM0218"}, temporal_presence="CURRENT",
                  temporal_time="this_month")
    d = PlannerDecision(action="tool", tool="student_attendance",
                        params={"time": "last_month"},
                        temporal=TemporalIntent(presence="PAST", time="last_month"))
    merged, tr = merge_follow_up(prev, d)
    assert merged.params.get("student") == "ARM0218"
    assert merged.temporal.time == "last_month"


def test_no_prev_state_is_noop():
    d = PlannerDecision(action="tool", tool="student_marks", params={"student": "ARM0218"},
                        temporal=TemporalIntent())
    merged, tr = merge_follow_up(None, d)
    assert merged.params == {"student": "ARM0218"}
    assert tr["inherited"] == []


def test_state_from_decision_captures_dimensions():
    d = PlannerDecision(action="tool", tool="student_marks",
                        params={"student": "ARM0242", "subject": "Science"},
                        temporal=TemporalIntent(presence="PAST", time={"month": "august"}))
    s = state_from_decision(d)
    assert s.domain == "exams"
    assert s.capability == "student_marks"
    assert s.entities.get("student") == "ARM0242"
    assert s.subject == "Science"
    assert s.temporal_presence == "PAST"


# ── End-to-end handle_turn: planner drops temporal on follow-up ───────────────


@pytest.mark.asyncio
async def test_e2e_followup_recovers_dropped_temporal(
    test_school: School, admin_user, db_session: AsyncSession, monkeypatch
):
    """Two real turns on one session; the SECOND planner call drops the time entirely.

    Carry-over must restore the previous PAST window so the integrity guard sees PAST (not a
    silent all-time/current answer) — the exact Phase 6 'what about September?' failure.
    """
    from app.modules.workspace.assistant import service as service_mod

    calls = {"n": 0}

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return PlannerDecision(
                action="tool", tool="fee_collection_period",
                params={"time": {"month": "august"}},
                temporal=TemporalIntent(presence="PAST", time={"month": "august"}),
            )
        # Follow-up: LLM dropped the temporal entirely.
        return PlannerDecision(
            action="tool", tool="fee_collection_period", params={},
            temporal=TemporalIntent(presence="NONE", time=None),
        )

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)

    r1 = await svc.handle_turn(current_user=user, text="fee collected in August", session_id=None)
    sid = r1["session_id"]
    assert r1["trace"]["semantic_temporality"] == "PAST"

    import uuid as _uuid
    r2 = await svc.handle_turn(
        current_user=user, text="what about receipts?", session_id=_uuid.UUID(sid)
    )
    # Carry-over restored August -> still PAST, integrity OK, NOT all-time.
    assert r2["trace"]["semantic_temporality"] == "PAST"
    assert "temporal:full" in r2["trace"]["carry_over"]["inherited"]
    assert r2["trace"]["temporal_integrity"] in ("OK", None)
    assert r2["block"]["kind"] == "metrics"  # answered, not blocked


@pytest.mark.asyncio
async def test_e2e_historical_followup_not_downgraded(
    test_school: School, admin_user, db_session: AsyncSession, monkeypatch
):
    """Historical relationship T1 -> elliptical T2 must NOT become current (P0.1 regression)."""
    from app.modules.workspace.assistant import service as service_mod

    calls = {"n": 0}

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return PlannerDecision(
                action="tool", tool="teachers_for_class",
                params={"class_label": "2A", "time": {"month": "august"}},
                temporal=TemporalIntent(presence="PAST", time={"month": "august"}),
            )
        return PlannerDecision(  # follow-up drops temporal
            action="tool", tool="teachers_for_class", params={"class_label": "2A"},
            temporal=TemporalIntent(presence="NONE", time=None),
        )

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)

    r1 = await svc.handle_turn(
        current_user=user, text="who was the class teacher of 2A in August?", session_id=None
    )
    import uuid as _uuid
    r2 = await svc.handle_turn(
        current_user=user, text="what about September?", session_id=_uuid.UUID(r1["session_id"])
    )
    # Still historical -> blocked, never a current-teacher answer.
    assert r2["trace"]["semantic_temporality"] == "PAST"
    assert r2["block"]["title"] == "Historical records not available"

@pytest.mark.asyncio
async def test_e2e_metric_switch_recovers_capability(
    test_school: School, admin_user, db_session: AsyncSession, monkeypatch
):
    """T1 'fee collected in August' -> T2 'how many receipts?' where the LLM returns a guide.

    P1.2a: capability + operation + time are recovered so the metric switch is answered
    (metrics block), not lost to a guide — the exact fu-metric-change benchmark failure.
    """
    from app.modules.workspace.assistant import service as service_mod

    calls = {"n": 0}

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return PlannerDecision(
                action="tool", tool="fee_collection_period",
                params={"time": {"month": "august"}},
                temporal=TemporalIntent(presence="PAST", time={"month": "august"}),
                operation="collection", metric="amount",
            )
        # Follow-up: LLM understood the metric but failed to pick a tool.
        return PlannerDecision(
            action="clarify", tool=None, params={},
            temporal=TemporalIntent(), metric="receipt_count",
        )

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)

    r1 = await svc.handle_turn(current_user=user, text="fee collected in August", session_id=None)
    import uuid as _uuid
    r2 = await svc.handle_turn(
        current_user=user, text="how many receipts were there?",
        session_id=_uuid.UUID(r1["session_id"]),
    )
    assert "capability" in r2["trace"]["carry_over"]["inherited"]
    assert r2["trace"]["capability"] == "fee_collection_period"
    assert r2["trace"]["semantic_temporality"] == "PAST"
    assert r2["block"]["kind"] == "metrics"  # answered with the (recovered) fee metrics
