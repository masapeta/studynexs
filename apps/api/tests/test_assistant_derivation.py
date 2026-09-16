"""Parameter derivation from canonical relationships (P1.3).

A capability that needs a parameter the conversation lacks explicitly (e.g. subject_toppers
needs class_label, but context only holds student=ARM0242) derives it from an authoritative
ERP relationship (student -> belongs_to -> class) instead of asking. Tested at the derivation
layer and end-to-end, including precedence, security, ambiguity, and historical safety.
"""

from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.examination import Exam, ExamMark, ExamType
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant import capabilities as cap
from app.modules.workspace.assistant.conversation import ConversationSemanticState
from app.modules.workspace.assistant.derivation import (
    SRC_DERIVED,
    derive_parameters,
)
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent


class _U:
    def __init__(self, school_id, user_id=None, role="super_admin"):
        self.id = str(user_id or school_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "T"


@pytest_asyncio.fixture
async def derive_school(db_session: AsyncSession, test_school: School):
    """One class (10 A) with a student ARM0242 who has English + Maths marks; a subject teacher."""
    ay = AcademicYear(school_id=test_school.id, year_label="2026-2027",
                      start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True)
    db_session.add(ay)
    await db_session.flush()

    teacher = User(school_id=test_school.id, username="dv_t", mobile="+919000000401",
                   full_name="Deepak Kumar", role=UserRole.CLASS_INCHARGE,
                   password_hash="x", is_active=True)
    db_session.add(teacher)
    await db_session.flush()
    cls = Class(school_id=test_school.id, grade="Class 10", section="A",
                academic_year_id=ay.id, class_incharge_id=teacher.id)
    other = Class(school_id=test_school.id, grade="Class 8", section="B",
                  academic_year_id=ay.id, class_incharge_id=teacher.id)
    db_session.add_all([cls, other])
    await db_session.flush()

    eng = Subject(school_id=test_school.id, name="English", class_id=cls.id)
    math = Subject(school_id=test_school.id, name="Mathematics", class_id=cls.id)
    db_session.add_all([eng, math])
    await db_session.flush()

    students = []
    for i, (adm, name, eng_mark) in enumerate(
        [("ARM0242", "Sai Rao", Decimal("88")), ("ARM0243", "Ivy Rao", Decimal("72"))]
    ):
        u = User(school_id=test_school.id, username=f"dv_s{i}", mobile=f"+9199000005{i}0",
                 full_name=name, role=UserRole.STUDENT, password_hash="x", is_active=True)
        db_session.add(u)
        await db_session.flush()
        s = Student(school_id=test_school.id, user_id=u.id, class_id=cls.id,
                    admission_no=adm, roll_no=str(i + 1))
        db_session.add(s)
        await db_session.flush()
        students.append((s, eng_mark))

    exam = Exam(school_id=test_school.id, class_id=cls.id, subject_id=eng.id,
                exam_type=ExamType.MID_TERM, title="Mid Term — English",
                total_marks=Decimal("100"), date=date(2026, 9, 1), created_by=teacher.id)
    db_session.add(exam)
    await db_session.flush()
    for s, mark in students:
        db_session.add(ExamMark(school_id=test_school.id, exam_id=exam.id, student_id=s.id,
                                marks_obtained=mark, grade_letter="A"))
    await db_session.flush()
    return {"class": cls, "other": other, "teacher": teacher, "eng": eng,
            "students": students}


# ── Derivation layer: student -> class_label ──────────────────────────────────


@pytest.mark.asyncio
async def test_derive_class_from_context_student(
    test_school: School, derive_school, db_session: AsyncSession
):
    """subject_toppers with no class but student=ARM0242 in context -> derive class 10 A."""
    prev = ConversationSemanticState(domain="exams", capability="student_marks",
                                     entities={"student": "ARM0242"}, subject="English")
    d = PlannerDecision(action="tool", tool="subject_toppers",
                        params={"subject": "English"}, temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d, prev, trace=trace)
    assert d.params.get("class_label") == "Class 10 A"
    prov = trace["param_provenance"][0]
    assert prov["parameter"] == "class_label"
    assert prov["source"] == SRC_DERIVED
    assert prov["derived_from"]["entity_type"] == "student"
    assert prov["derived_from"]["relationship"] == "belongs_to"


@pytest.mark.asyncio
async def test_explicit_class_not_overridden_by_derivation(
    test_school: School, derive_school, db_session: AsyncSession
):
    """Explicit class must win over a derivable one (precedence + conflict, §25/§26)."""
    prev = ConversationSemanticState(domain="exams", entities={"student": "ARM0242"})
    d = PlannerDecision(action="tool", tool="subject_toppers",
                        params={"class_label": "Class 8 B", "subject": "English"},
                        temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d, prev, trace=trace)
    assert d.params["class_label"] == "Class 8 B"  # explicit kept, NOT replaced with 10 A
    assert "param_provenance" not in trace


@pytest.mark.asyncio
async def test_no_student_no_derivation(
    test_school: School, derive_school, db_session: AsyncSession
):
    prev = ConversationSemanticState(domain="exams")
    d = PlannerDecision(action="tool", tool="subject_toppers",
                        params={"subject": "English"}, temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d, prev, trace=trace)
    assert "class_label" not in d.params  # nothing to derive from -> stays missing (clarify later)


@pytest.mark.asyncio
async def test_ambiguous_student_does_not_derive(
    test_school: School, derive_school, db_session: AsyncSession
):
    """Two students named 'Rao' by first token? Use a name that matches 2 -> no guess."""
    prev = ConversationSemanticState(domain="exams", entities={"student": "Rao"})
    d = PlannerDecision(action="tool", tool="subject_toppers",
                        params={"subject": "English"}, temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d, prev, trace=trace)
    # "Rao" matches both Sai Rao and Ivy Rao -> ambiguous -> no derivation (§14).
    assert "class_label" not in d.params


# ── End-to-end deep pivot: marks -> English -> who scored highest ──────────────


@pytest.mark.asyncio
async def test_e2e_deep_pivot_derives_class_and_ranks(
    test_school: School, derive_school, admin_user, db_session: AsyncSession, monkeypatch
):
    """3-turn chain: the pivot to subject_toppers derives class from the student and ranks."""
    from app.modules.workspace.assistant import service as service_mod

    calls = {"n": 0}

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return PlannerDecision(action="tool", tool="student_marks",
                                   params={"student": "ARM0242"}, temporal=TemporalIntent(),
                                   operation="lookup", metric="marks")
        if calls["n"] == 2:
            return PlannerDecision(action="tool", tool="student_marks",
                                   params={"student": "ARM0242", "subject": "English"},
                                   temporal=TemporalIntent(), operation="lookup", metric="marks")
        # Turn 3: pivot to ranking; planner names no class (the derivation gap).
        return PlannerDecision(action="tool", tool="subject_toppers",
                               params={"subject": "English"}, temporal=TemporalIntent(),
                               operation="ranking")

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)

    import uuid as _uuid
    r1 = await svc.handle_turn(current_user=user, text="show ARM0242's marks", session_id=None)
    sid = _uuid.UUID(r1["session_id"])
    await svc.handle_turn(current_user=user, text="what about English?", session_id=sid)
    r3 = await svc.handle_turn(current_user=user, text="who scored highest?", session_id=sid)

    assert r3["trace"]["capability"] == "subject_toppers"
    assert r3["trace"]["param_provenance"], "class should have been derived"
    assert r3["trace"]["param_provenance"][0]["source"] == SRC_DERIVED
    assert r3["block"]["kind"] == "table"  # ranked, NOT a clarify
    assert r3["block"]["rows"][0]["name"] == "Sai Rao"  # 88 > 72


# ── Single-turn derivation ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_single_turn_class_results_from_student(
    test_school: School, derive_school, db_session: AsyncSession
):
    """No prior turn; the derivation still fills class from an explicit in-turn student."""
    prev = None
    d = PlannerDecision(action="tool", tool="class_results",
                        params={"student": "ARM0242"}, temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d,
                            ConversationSemanticState() if prev is None else prev, trace=trace)
    assert d.params.get("class_label") == "Class 10 A"


# ── Security: derived class still authorized ──────────────────────────────────


@pytest.mark.asyncio
async def test_derived_class_still_authorized(
    test_school: School, derive_school, db_session: AsyncSession
):
    """A teacher NOT assigned to the derived class must still be denied downstream (P1.1)."""
    # A subject teacher of nothing (no mappings, not incharge) -> scoped_only, no classes.
    outsider = User(school_id=test_school.id, username="dv_out", mobile="+919000000999",
                    full_name="Outsider", role=UserRole.TEACHER, password_hash="x",
                    is_active=True)
    db_session.add(outsider)
    await db_session.flush()
    user = _U(test_school.id, user_id=outsider.id, role="teacher")
    # class derived to 10 A, but this teacher can't access it.
    block = await cap.class_results(db_session, user, {"class_label": "Class 10 A"})
    assert block["title"] == "Not available"


# ── Historical safety: derivation does not run for PAST (handled upstream) ─────


@pytest.mark.asyncio
async def test_derivation_skipped_for_historical(
    test_school: School, derive_school, admin_user, db_session: AsyncSession, monkeypatch
):
    """A historical pivot must not derive a current class; it stays blocked (P0.1/§15)."""
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        # historical relationship pivot with no class named
        return PlannerDecision(action="tool", tool="teachers_for_class",
                               params={"student": "ARM0242"},
                               temporal=TemporalIntent(presence="PAST", time={"month": "august"}))

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)
    r = await svc.handle_turn(
        current_user=user, text="who taught his class in August?", session_id=None
    )
    # PAST + current-state teachers cap -> blocked; derivation must not have produced a table.
    assert r["block"]["kind"] == "not_found"
    assert r["trace"].get("param_provenance") is None
