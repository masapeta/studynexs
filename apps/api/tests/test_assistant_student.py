"""Student conversational capabilities (Milestone 2).

A student asks about THEIR OWN learning in the existing chat. These tests prove:
  - the four student tools return grounded, structured blocks for the authenticated student;
  - identity is the authenticated student only — no student_id is accepted from params, and a
    spoofed id cannot change the authorized identity;
  - a student can reach only their own records; cross-student / cross-tenant is non-leaky;
  - staff and parent tools are invisible to students (and student tools invisible to them);
  - the metered ask_tutor path reuses StudentCopilotService.ask (one tutor_explain credit,
    one grounded LLM call) with no double charge;
  - the full handle_turn path routes student requests to the intended capabilities.

Deterministic tools (daily plan / weak topics / lesson) incur no LLM cost. The tutor test
stubs the LLM at the copilot module (the repo's established pattern) — it proves metering and
response handling, NOT real-LLM routing accuracy.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.ai_usage import AIUsage
from app.db.models.concept_card import ConceptCard, ConceptCardStatus
from app.db.models.curriculum_pack import (
    CurriculumChapter,
    CurriculumPack,
    CurriculumTopic,
    PackStatus,
)
from app.db.models.knowledge_graph import CurriculumConcept
from app.db.models.mastery import MasteryTrend, StudentTopicMastery
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.embeddings.stub_provider import StubEmbeddingProvider
from app.modules.ai.gateway import LLMResult
from app.modules.knowledge_graph.services.graph_service import KnowledgeGraphService
from app.modules.knowledge_graph.services.student_weak_concept_service import (
    StudentWeakConceptService,
)
from app.modules.workspace.assistant import capabilities as cap
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent

_COPILOT_LLM = "app.modules.tutor.services.student_copilot_service.generate_llm"


@pytest.fixture(autouse=True)
def _stub_embeddings(monkeypatch):
    """Force the offline stub embedder so daily-plan/tutor retrieval makes no live model call.

    daily_plan and ask_tutor run RAG retrieval, which EMBEDS the query — a real external call.
    Patching the embedding-provider factory (mirrors the no-key offline fallback) keeps these
    tests hermetic. The generative tutor LLM is stubbed separately where a turn actually asks.
    """
    monkeypatch.setattr(
        "app.modules.ai.embeddings.service.get_embedding_provider",
        lambda *a, **k: StubEmbeddingProvider(),
    )
    yield


class _U:
    """CurrentUser stand-in (id/school_id/role/full_name/tenant_slug)."""

    def __init__(self, user_id, school_id, role):
        self.id = str(user_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "Student"
        self.tenant_slug = None


@pytest_asyncio.fixture
async def student_learning(db_session: AsyncSession):
    """One student with a weak concept + approved ConceptCard so learning reads are grounded.

    Returns the student's own user + a SECOND student (different family/user) in the same
    school to prove self-only isolation, plus a second school for cross-tenant checks.
    """
    school = School(
        name="Nagar School", code="NAG", tenant_slug="nagar", board="SSC",
        contact_email="a@n.com", contact_phone="+910000000000", is_active=True,
    )
    db_session.add(school)
    await db_session.flush()
    ay = AcademicYear(
        school_id=school.id, year_label="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True,
    )
    db_session.add(ay)
    await db_session.flush()
    cls = Class(school_id=school.id, grade="10", section="A", academic_year_id=ay.id)
    teacher = User(school_id=school.id, mobile="+910000000001", full_name="Teacher",
                   role=UserRole.TEACHER, is_active=True)
    me_user = User(school_id=school.id, mobile="+910000000002", full_name="Aarav",
                   role=UserRole.STUDENT, is_active=True)
    other_user = User(school_id=school.id, mobile="+910000000003", full_name="Diya",
                      role=UserRole.STUDENT, is_active=True)
    db_session.add_all([cls, teacher, me_user, other_user])
    await db_session.flush()
    subject = Subject(school_id=school.id, name="Maths", class_id=cls.id)
    db_session.add(subject)
    await db_session.flush()
    me = Student(school_id=school.id, user_id=me_user.id, class_id=cls.id, admission_no="A1")
    other = Student(school_id=school.id, user_id=other_user.id, class_id=cls.id,
                    admission_no="A2")
    db_session.add_all([me, other])
    await db_session.flush()

    pack = CurriculumPack(
        school_id=school.id, class_id=cls.id, subject_id=subject.id,
        academic_year_id=ay.id, board="SSC", created_by=teacher.id,
        status=PackStatus.APPROVED, approved_by=teacher.id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(pack)
    await db_session.flush()
    chapter = CurriculumChapter(
        school_id=school.id, pack_id=pack.id, number="1", title="Algebra", order_index=0
    )
    db_session.add(chapter)
    await db_session.flush()
    topic = CurriculumTopic(
        school_id=school.id, chapter_id=chapter.id, title="Linear Equations",
        concepts=["slope"], order_index=0,
    )
    db_session.add(topic)
    await db_session.flush()
    await KnowledgeGraphService(db_session).build_spine_from_pack(
        school_id=school.id, pack_id=pack.id
    )
    await StudentWeakConceptService(db_session).sync_from_ledger(
        school_id=school.id, class_id=cls.id, subject_id=subject.id, academic_year_id=ay.id,
        ledger_rows=[{
            "student_id": me.id, "topic": "linear equations",
            "topic_display": "Linear Equations", "mastery_pct": 48.0,
            "class_avg_pct": 72.0, "assessments_count": 2,
            "last_assessed_on": date(2026, 7, 1), "trend": MasteryTrend.STABLE, "history": [],
        }],
    )
    # Mastery row so list_recommendations surfaces the weak topic (deterministic, no LLM).
    db_session.add(StudentTopicMastery(
        school_id=school.id, student_id=me.id, class_id=cls.id, subject_id=subject.id,
        academic_year_id=ay.id, topic="linear equations", topic_display="Linear Equations",
        mastery_pct=48.0, assessments_count=2, trend=MasteryTrend.STABLE,
    ))
    await db_session.flush()
    concept = (
        await db_session.execute(
            select(CurriculumConcept).where(CurriculumConcept.slug == "slope")
        )
    ).scalar_one()
    db_session.add(ConceptCard(
        school_id=school.id, pack_id=pack.id, concept_id=concept.id,
        title="Slope", explanation="Slope is rise over run.",
        status=ConceptCardStatus.APPROVED, created_by=teacher.id,
        approved_by=teacher.id, approved_at=datetime.now(timezone.utc),
    ))
    await db_session.flush()

    return {
        "school": school, "me_user": me_user, "other_user": other_user,
        "me_id": me.id, "other_id": other.id, "concept_slug": "slope",
    }


# ── Deterministic student capabilities (no LLM, no credits) ─────────────────────


@pytest.mark.asyncio
async def test_student_daily_plan(student_learning, db_session: AsyncSession):
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    block = await cap.my_daily_plan(db_session, user, {})
    assert block["kind"] in ("metrics", "guide")
    # Grounded on the seeded weak concept -> a ready plan with the topic.
    assert block["kind"] == "metrics"
    assert "Linear Equations" in (block.get("subtitle") or "") or "Study" in block["title"]


@pytest.mark.asyncio
async def test_student_weak_topics(student_learning, db_session: AsyncSession):
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    block = await cap.my_weak_topics(db_session, user, {})
    assert block["kind"] == "table"
    topics = " ".join(r.get("topic", "") for r in block["rows"])
    assert "Linear Equations" in topics


@pytest.mark.asyncio
async def test_student_lesson_self(student_learning, db_session: AsyncSession):
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    block = await cap.my_lesson(db_session, user, {"topic": "slope"})
    assert block["kind"] == "document"
    assert "Slope" in block["title"] or "slope" in block["message"].lower()


@pytest.mark.asyncio
async def test_student_with_no_learning_is_honest(student_learning, db_session: AsyncSession):
    """The OTHER student has no assessed evidence -> honest empty plan, no fabricated mastery.

    `list_recommendations` returns a clearly-labelled starter/sample lesson for a student with
    no evidence (never a fabricated mastery %); `get_daily_plan` returns the honest empty guide.
    """
    user = _U(student_learning["other_user"].id, student_learning["school"].id, "student")
    plan = await cap.my_daily_plan(db_session, user, {})
    assert plan["kind"] == "guide"  # no evidence -> honest "no learning action yet"
    weak = await cap.my_weak_topics(db_session, user, {})
    assert weak["kind"] == "table"
    # No fabricated mastery figures for a student with no assessed evidence.
    assert all(r.get("mastery_pct") is None for r in weak["rows"])
    assert "sample" in " ".join(r.get("reason", "").lower() for r in weak["rows"])


# ── Metered AI tutor ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_ask_tutor_meters_one_credit(
    student_learning, db_session: AsyncSession, monkeypatch
):
    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({
                "answer": "Slope is how steep a line is — rise over run.",
                "citations": [],
                "follow_up_hints": ["Try y = 2x + 1"],
            }),
            model="stub", provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)
    school_id = student_learning["school"].id
    user = _U(student_learning["me_user"].id, school_id, "student")

    before = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id, AIUsage.purpose_tag == "tutor_explain"
        )
    )).scalar_one())

    block = await cap.ask_tutor(
        db_session, user, {"question": "Can you explain slope to me?"}
    )
    assert block["kind"] == "document"
    assert "slope" in block["message"].lower()

    after = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id, AIUsage.purpose_tag == "tutor_explain"
        )
    )).scalar_one())
    # Exactly one tutor_explain credit charged — no double charge from assistant orchestration.
    assert after - before == 1


@pytest.mark.asyncio
async def test_student_ask_tutor_short_question_clarifies_without_charge(
    student_learning, db_session: AsyncSession
):
    school_id = student_learning["school"].id
    user = _U(student_learning["me_user"].id, school_id, "student")
    block = await cap.ask_tutor(db_session, user, {"question": "hi"})
    assert block["kind"] == "clarify"
    charged = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id
        )
    )).scalar_one())
    assert charged == 0  # too-short question never reaches the metered path


# ── Identity & isolation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_spoofed_student_id_ignored(student_learning, db_session: AsyncSession):
    """A params-supplied student_id must not change the authorized (self) identity."""
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    block = await cap.my_weak_topics(
        db_session, user, {"student_id": str(student_learning["other_id"])}
    )
    # Resolves to the caller's OWN record; the foreign id is never consulted.
    assert block["kind"] == "table"
    topics = " ".join(r.get("topic", "") for r in block["rows"])
    assert "Linear Equations" in topics  # own weak topic, not the other student's


@pytest.mark.asyncio
async def test_other_student_cannot_see_my_weak_topic(
    student_learning, db_session: AsyncSession
):
    """The other student never sees the first student's weak topic (isolation), only a sample."""
    user = _U(student_learning["other_user"].id, student_learning["school"].id, "student")
    block = await cap.my_weak_topics(db_session, user, {})
    assert block["kind"] == "table"
    topics = " ".join(r.get("topic", "") for r in block["rows"])
    assert "Linear Equations" not in topics  # never the other student's evidence


@pytest.mark.asyncio
async def test_cross_tenant_student_has_no_profile(
    student_learning, db_session: AsyncSession
):
    """The student's user id presented against a DIFFERENT school resolves to no profile."""
    other = School(name="Other", code="OTH2", tenant_slug="other2")
    db_session.add(other)
    await db_session.flush()
    user = _U(student_learning["me_user"].id, other.id, "student")
    block = await cap.my_daily_plan(db_session, user, {})
    assert block["kind"] == "not_found"
    assert block["title"] == "No student profile"


# ── Role visibility ─────────────────────────────────────────────────────────────


def test_student_tools_scoped_to_student_role():
    from app.modules.workspace.assistant.tools import tools_for_role

    student_names = {t.name for t in tools_for_role("student")}
    assert student_names == {
        "my_daily_plan", "my_weak_topics", "my_lesson", "ask_tutor",
    }
    # Staff and parent tools are invisible to students.
    assert "class_results" not in student_names
    assert "my_child_fees" not in student_names
    # Student tools are invisible to staff and parents.
    for role in ("teacher", "class_incharge", "admin", "super_admin", "parent"):
        names = {t.name for t in tools_for_role(role)}
        assert not (names & student_names)


def test_parent_tools_unchanged_by_student_slice():
    from app.modules.workspace.assistant.tools import tools_for_role

    parent_names = {t.name for t in tools_for_role("parent")}
    assert parent_names == {
        "my_children_overview", "my_child_attendance", "my_child_progress", "my_child_fees",
    }


def test_registries_still_valid():
    from app.modules.workspace.assistant.contracts import validate_registries

    validate_registries()


# ── Full assistant turn (planner -> student tool -> service -> block) ───────────


@pytest.mark.asyncio
async def test_full_turn_student_weak_topics(
    student_learning, db_session: AsyncSession, monkeypatch
):
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="my_weak_topics",
                               params={}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    r = await svc.handle_turn(
        current_user=user, text="which topics am I weak in?", session_id=None
    )
    assert r["block"]["kind"] == "table"
    assert r["trace"]["capability"] == "my_weak_topics"
    topics = " ".join(row.get("topic", "") for row in r["block"]["rows"])
    assert "Linear Equations" in topics


@pytest.mark.asyncio
async def test_full_turn_student_cannot_invoke_staff_tool(
    student_learning, db_session: AsyncSession, monkeypatch
):
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="class_results",
                               params={"class_label": "10A"}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    r = await svc.handle_turn(
        current_user=user, text="show me class 10A results", session_id=None
    )
    assert r["block"]["kind"] == "guide"  # staff tool not allowed_for(student) -> guide

# ── Tutor-specific rate limit (Milestone 3) ─────────────────────────────────────
# The limiter is enforced INSIDE ask_tutor before the metered call. Both the limiter guard
# and check_rate_limit no-op under ENVIRONMENT==testing, so these tests force a non-testing,
# rate-limit-enabled settings and inject a counting fake Redis + the real fixed-window logic.


class _FakeRedis:
    """Minimal async Redis implementing the INCR+EXPIRE eval the limiter uses."""

    def __init__(self):
        self.counts: dict[str, int] = {}
        self.fail = False

    async def eval(self, _script, _nkeys, key, _window):
        if self.fail:
            raise RuntimeError("redis down")
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]


def _force_rate_limited_settings(monkeypatch, fake_redis):
    """Make the tutor limiter active (non-testing + enabled) with a fake Redis + fresh settings."""
    from app.core import dependencies as deps
    from app.core.config import Environment, get_settings

    base = get_settings()

    class _S:
        RATE_LIMIT_ENABLED = True
        ENVIRONMENT = Environment.PRODUCTION
        REDIS_RATE_LIMIT_PREFIX = base.REDIS_RATE_LIMIT_PREFIX

    # _enforce_tutor_rate_limit does `from app.core.config import get_settings` -> patch source.
    monkeypatch.setattr("app.core.config.get_settings", lambda: _S())
    # check_rate_limit reads its OWN module-level settings for the testing short-circuit.
    monkeypatch.setattr(deps, "settings", _S())
    monkeypatch.setattr(deps, "_redis_pool", fake_redis)

    async def _fake_get_redis():
        return fake_redis

    monkeypatch.setattr(deps, "get_redis", _fake_get_redis)


@pytest.mark.asyncio
async def test_ask_tutor_allowed_within_budget_then_rate_limited(
    student_learning, db_session: AsyncSession, monkeypatch
):
    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({"answer": "Slope is rise over run.", "citations": [],
                             "follow_up_hints": []}),
            model="stub", provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)
    fake = _FakeRedis()
    _force_rate_limited_settings(monkeypatch, fake)
    school_id = student_learning["school"].id
    user = _U(student_learning["me_user"].id, school_id, "student")

    # 20 requests are permitted (each reaches the tutor and returns a document block).
    for _ in range(20):
        block = await cap.ask_tutor(db_session, user, {"question": "explain slope please"})
        assert block["kind"] == "document"

    # The 21st in the same window is rate-limited BEFORE the metered call (guide, not a charge).
    charged_before = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id, AIUsage.purpose_tag == "tutor_explain"
        )
    )).scalar_one())
    limited = await cap.ask_tutor(db_session, user, {"question": "explain slope please"})
    assert limited["kind"] == "guide"
    assert "limit" in limited["message"].lower()
    charged_after = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id, AIUsage.purpose_tag == "tutor_explain"
        )
    )).scalar_one())
    assert charged_after == charged_before  # rate-limited call never charged


@pytest.mark.asyncio
async def test_ask_tutor_limiter_keys_by_school_and_user(
    student_learning, db_session: AsyncSession, monkeypatch
):
    async def _fake_llm(*_a, **_k):
        return LLMResult(
            text=json.dumps({"answer": "ok", "citations": [], "follow_up_hints": []}),
            model="stub", provider="stub",
        )

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)
    fake = _FakeRedis()
    _force_rate_limited_settings(monkeypatch, fake)
    school_id = student_learning["school"].id
    user = _U(student_learning["me_user"].id, school_id, "student")
    await cap.ask_tutor(db_session, user, {"question": "explain slope please"})
    from app.core.config import get_settings

    prefix = get_settings().REDIS_RATE_LIMIT_PREFIX
    expected = f"{prefix}assistant_tutor:{user.school_id}:{user.id}"
    assert expected in fake.counts  # distinct key, keyed by authenticated school + user
    # Never shares a counter with the workspace_turn or /ask (student_copilot) limiters.
    assert not any("workspace_turn" in k or "student_copilot" in k for k in fake.counts)


@pytest.mark.asyncio
async def test_ask_tutor_redis_failure_fails_closed_no_charge(
    student_learning, db_session: AsyncSession, monkeypatch
):
    async def _fake_llm(*_a, **_k):  # must never run on a fail-closed path
        raise AssertionError("tutor LLM must not run when the limiter fails closed")

    monkeypatch.setattr(_COPILOT_LLM, _fake_llm)
    fake = _FakeRedis()
    fake.fail = True
    _force_rate_limited_settings(monkeypatch, fake)
    school_id = student_learning["school"].id
    user = _U(student_learning["me_user"].id, school_id, "student")

    before = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id
        )
    )).scalar_one())
    block = await cap.ask_tutor(db_session, user, {"question": "explain slope please"})
    assert block["kind"] == "error"  # fail-closed: honest error, not a silent permit
    after = int((await db_session.execute(
        select(func.coalesce(func.sum(AIUsage.credits_charged), 0)).where(
            AIUsage.school_id == school_id
        )
    )).scalar_one())
    assert after == before  # no credit charged when the limiter fails closed


@pytest.mark.asyncio
async def test_deterministic_student_tools_do_not_consume_tutor_budget(
    student_learning, db_session: AsyncSession, monkeypatch
):
    """weak_topics / lesson / daily_plan must never touch the tutor limiter counter."""
    fake = _FakeRedis()
    _force_rate_limited_settings(monkeypatch, fake)
    user = _U(student_learning["me_user"].id, student_learning["school"].id, "student")
    await cap.my_weak_topics(db_session, user, {})
    await cap.my_lesson(db_session, user, {})
    await cap.my_daily_plan(db_session, user, {})
    assert not any("assistant_tutor" in k for k in fake.counts)  # no tutor budget consumed
