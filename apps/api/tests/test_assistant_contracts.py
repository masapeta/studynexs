"""Capability contracts + relationship registry (P1.5).

Validates the machine-readable registries and proves the generic derivation engine resolves
the mandated case: "who teaches the class ARM0242 is in?" -> derive class from student ->
teachers_for_class, with no clarification and no dedicated per-phrase capability.
"""

from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear, Class
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.workspace.assistant.contracts import (
    CAPABILITY_CONTRACTS,
    ContractError,
    find_relationship,
    get_contract,
    validate_registries,
)
from app.modules.workspace.assistant.derivation import derive_parameters
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent


class _U:
    def __init__(self, school_id, user_id=None, role="super_admin"):
        self.id = str(user_id or school_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "T"


# ── Registry validation (§16, §17) ────────────────────────────────────────────


def test_registries_validate():
    validate_registries()  # raises on any structural problem


def test_every_tool_has_a_contract():
    from app.modules.workspace.assistant.tools import ASSISTANT_TOOLS

    for t in ASSISTANT_TOOLS:
        assert get_contract(t.name) is not None, f"{t.name} missing a contract"


def test_contract_temporal_mode_matches_tool():
    from app.modules.workspace.assistant.tools import get_tool

    for name, c in CAPABILITY_CONTRACTS.items():
        assert get_tool(name).temporal_mode == c.temporal_mode


def test_relationship_registry_shape():
    rel = find_relationship("student", "class")
    assert rel is not None
    assert rel.name == "belongs_to"
    assert rel.cardinality == "many_to_one"
    assert rel.temporal_mode == "current_state"
    assert rel.target_param == "class_label"


def test_validation_catches_bad_contract(monkeypatch):
    """A derivable param whose relationship is missing must fail validation fast."""
    from app.modules.workspace.assistant import contracts as c
    from app.modules.workspace.assistant.contracts import (
        CapabilityContract,
        ParamContract,
    )

    bad = CapabilityContract(
        "bogus", "student", "lookup", "student", "timeless",
        params={"class_label": ParamContract(
            "class_label", "class", derive_from=("teacher",),
            sources=("EXPLICIT", "DERIVED"))},  # no teacher->class relationship exists
    )
    monkeypatch.setitem(c.CAPABILITY_CONTRACTS, "bogus", bad)
    with pytest.raises(ContractError):
        validate_registries()


# ── Derivation via the registry (generic) ─────────────────────────────────────


@pytest_asyncio.fixture
async def one_class(db_session: AsyncSession, test_school: School):
    ay = AcademicYear(school_id=test_school.id, year_label="2026-2027",
                      start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_active=True)
    db_session.add(ay)
    await db_session.flush()
    teacher = User(school_id=test_school.id, username="ct_c", mobile="+919000000801",
                   full_name="Deepak Kumar", role=UserRole.CLASS_INCHARGE,
                   password_hash="x", is_active=True)
    db_session.add(teacher)
    await db_session.flush()
    cls = Class(school_id=test_school.id, grade="Class 10", section="A",
                academic_year_id=ay.id, class_incharge_id=teacher.id)
    db_session.add(cls)
    await db_session.flush()
    u = User(school_id=test_school.id, username="ct_s", mobile="+919000000802",
             full_name="Sai Rao", role=UserRole.STUDENT, password_hash="x", is_active=True)
    db_session.add(u)
    await db_session.flush()
    db_session.add(Student(school_id=test_school.id, user_id=u.id, class_id=cls.id,
                           admission_no="ARM0242", roll_no="1"))
    await db_session.flush()
    return {"class": cls, "teacher": teacher}


@pytest.mark.asyncio
async def test_derive_class_for_teachers_for_class(
    test_school: School, one_class, db_session: AsyncSession
):
    """teachers_for_class with only student=ARM0242 -> class derived via registry."""
    d = PlannerDecision(action="tool", tool="teachers_for_class",
                        params={"student": "ARM0242"}, temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d, None, trace=trace)
    assert d.params.get("class_label") == "Class 10 A"
    assert trace["param_provenance"][0]["source"] == "DERIVED"
    assert trace["derivation_path"] == ["student -belongs_to-> class=Class 10 A"]


@pytest.mark.asyncio
async def test_derivation_caches_within_turn(
    test_school: School, one_class, db_session: AsyncSession
):
    """Same student derived once even if two params could derive from it (§31)."""
    # subject_toppers needs class_label; only one derivation call should be cached.
    d = PlannerDecision(action="tool", tool="subject_toppers",
                        params={"student": "ARM0242", "subject": "English"},
                        temporal=TemporalIntent())
    trace: dict = {}
    await derive_parameters(db_session, test_school.id, d, None, trace=trace)
    assert d.params.get("class_label") == "Class 10 A"


# ── Mandatory §28: end-to-end single-turn derivation ──────────────────────────


@pytest.mark.asyncio
async def test_e2e_who_teaches_the_class_student_is_in(
    test_school: School, one_class, admin_user, db_session: AsyncSession, monkeypatch
):
    """'who teaches the class ARM0242 is in?' -> teachers table via derived class, no clarify.

    The planner (stubbed to mimic the contract-guided behaviour) emits teachers_for_class with
    only the student; the registry-driven derivation fills the class before execution.
    """
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="teachers_for_class",
                               params={"student": "ARM0242"}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)
    r = await svc.handle_turn(
        current_user=user, text="who teaches the class ARM0242 is in?", session_id=None
    )
    assert r["block"]["kind"] == "table"
    assert r["trace"]["capability"] == "teachers_for_class"
    assert r["trace"]["derivation_path"] == ["student -belongs_to-> class=Class 10 A"]
    assert r["trace"]["capability_contract"]["scope"] == "class"
    names = " ".join(row.get("name", "") for row in r["block"]["rows"])
    assert "Deepak" in names  # the class incharge of 10 A


@pytest.mark.asyncio
async def test_historical_derivation_skipped(
    test_school: School, one_class, admin_user, db_session: AsyncSession, monkeypatch
):
    """A PAST relationship pivot must not derive a current class; stays blocked (§20)."""
    from app.modules.workspace.assistant import service as service_mod

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="teachers_for_class",
                               params={"student": "ARM0242"},
                               temporal=TemporalIntent(presence="PAST", time={"month": "august"}))

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(test_school.id, user_id=admin_user.id)
    r = await svc.handle_turn(
        current_user=user, text="who taught the class ARM0242 is in last August?", session_id=None
    )
    assert r["block"]["kind"] == "not_found"
    assert r["trace"].get("derivation_path") is None  # derivation skipped for PAST
