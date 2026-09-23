"""P1.8 — cross-school SEMANTIC variance.

P1.7 proved terminology/labels are configuration. P1.8 proves SchoolPack expresses *real
semantic differences* — attendance calculation policy, grading interpretation, and academic
period concept-vs-label — over the SAME universal runtime, plus the adapter seam that keeps
the semantic relationship layer separate from physical storage (§19/§20).

Layer boundary asserted here (spec §21):
  universal semantic relationship  -> contracts.RELATIONSHIPS (student -belongs_to-> class)
  configured semantics/business    -> SchoolPack (attendance policy, grading, period mapping)
  physical schema detail           -> the relationship RESOLVER (adapter), never the registry
  authorization                    -> server-side (unchanged by any pack)
"""

from __future__ import annotations

import inspect
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.attendance import Attendance, AttendanceStatus
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.workspace.assistant.capabilities import low_attendance_students, student_attendance
from app.modules.workspace.assistant.contracts import Relationship, find_relationship
from app.modules.workspace.assistant.school_pack import (
    SCHOOL_A_PACK,
    SCHOOL_B_PACK,
    SCHOOL_C_PACK,
    SCHOOL_MINIMAL_PACK,
    AttendancePolicy,
    get_school_pack,
    use_school_pack,
)


class _User:
    def __init__(self, school_id, role="super_admin", user_id=None, tenant_slug="test"):
        self.school_id = str(school_id)
        self.role = role
        self.id = str(user_id or school_id)
        self.full_name = "Variance Admin"
        self.tenant_slug = tenant_slug


# ── §4 attendance policy: same counts, different configured denominator/credit ──────────


def test_attendance_policy_scores_same_counts_differently_per_school():
    counts = {"present": 10, "late": 2, "half_day": 2, "absent": 1}
    # Default/A: present+late+half_day credited @1.0 over ALL 15 -> 14/15.
    assert SCHOOL_A_PACK.attendance_percentage(counts) == round(14 / 15 * 100, 1)
    # B: late counts as 0.5 -> (10 + 1 + 2)/15 = 13/15.
    assert SCHOOL_B_PACK.attendance_percentage(counts) == round(13 / 15 * 100, 1)
    # C: half_day EXCLUDED from denominator -> base 13 (10+2+1), credited 12 -> 12/13.
    assert SCHOOL_C_PACK.attendance_percentage(counts) == round(12 / 13 * 100, 1)


def test_attendance_policy_empty_base_is_none_not_zero():
    assert SCHOOL_A_PACK.attendance_percentage({}) is None
    assert SCHOOL_C_PACK.attendance_percentage({"half_day": 5}) is None  # all excluded


def test_default_attendance_matches_legacy_convention():
    """Default policy reproduces the pre-P1.8 credited/total convention exactly."""
    counts = {"present": 8, "late": 1, "half_day": 1, "absent": 2}
    legacy = round((8 + 1 + 1) / 12 * 100, 1)
    assert get_school_pack().attendance_percentage(counts) == legacy


# ── §6/§7 grading interpretation differs by configuration ───────────────────────────────


def test_same_mark_different_grade_per_school():
    assert get_school_pack().grade_letter(72) == "B"
    assert SCHOOL_B_PACK.grade_letter(72) == "A"
    assert SCHOOL_C_PACK.grade_letter(72) == "Merit"


def test_missing_grading_is_honest_never_borrowed():
    assert SCHOOL_MINIMAL_PACK.supports_grading is False
    assert SCHOOL_MINIMAL_PACK.grade_letter(72) is None


# ── §9/§12 academic period: concept vs label, no invented equivalence ───────────────────


def test_period_concept_reverse_maps_only_configured_words():
    # School A calls the 'term' concept "Term"; B calls it "Semester".
    assert SCHOOL_A_PACK.period_concept("Term") == "term"
    assert SCHOOL_B_PACK.period_concept("Semester") == "term"
    # A never configured "Semester" -> no invented Term==Semester equivalence (§12).
    assert SCHOOL_A_PACK.period_concept("Semester") is None
    # B never configured "Term".
    assert SCHOOL_B_PACK.period_concept("Term") is None


def test_period_label_is_config_driven():
    assert SCHOOL_A_PACK.period_term("term") == "Term"
    assert SCHOOL_B_PACK.period_term("term") == "Semester"
    assert SCHOOL_C_PACK.period_term("term") == "Annual"


# ── §13 capability contracts hold no business formulas / thresholds ─────────────────────


def test_contracts_contain_no_attendance_or_grading_business_rules():
    from app.modules.workspace.assistant.contracts import CAPABILITY_CONTRACTS

    blob = repr(CAPABILITY_CONTRACTS)
    for banned in ("denominator", "credit", "half_day", "0.5", "Merit", "Distinction", "72"):
        assert banned not in blob, f"contract registry leaks business rule {banned!r}"


# ── §28 hard-coding scan: no attendance formula / grade threshold in universal modules ──


def test_universal_modules_have_no_business_rule_constants():
    from app.modules.workspace.assistant import conversation, derivation, planner

    # These engines must not encode any attendance credit weights or grade thresholds.
    for module in (planner, conversation, derivation):
        src = inspect.getsource(module)
        for banned in ("half_day", "0.5", '"present"', "grade_letter", "attendance_percentage"):
            assert banned not in src, f"{module.__name__} encodes business rule {banned!r}"


# ── §19/§20 adapter seam: same universal relationship over different physical schemas ────


@pytest.mark.asyncio
async def test_relationship_resolver_is_the_only_place_physical_schema_lives():
    """The registry exposes a semantic edge; a DIFFERENT physical schema is a different
    resolver, and the derivation engine consumes it unchanged (§19/§20)."""
    from app.modules.workspace.assistant import derivation

    calls: list[str] = []

    async def adapter_a(db, school_id, token):  # physical: student.class_id
        calls.append("A")
        return "Grade 1 A", {"relationship": "belongs_to", "to": "class"}

    async def adapter_b(db, school_id, token):  # physical: student_enrollment.class_id
        calls.append("B")
        return "Grade 1 A", {"relationship": "belongs_to", "to": "class"}

    rel_a = Relationship(
        name="belongs_to", source="student", target="class",
        cardinality="many_to_one", temporal_mode="current_state",
        resolver=adapter_a, target_param="class_label",
    )
    rel_b = Relationship(
        name="belongs_to", source="student", target="class",
        cardinality="many_to_one", temporal_mode="current_state",
        resolver=adapter_b, target_param="class_label",
    )

    # The derivation engine only knows find_relationship + .resolver; swapping the adapter
    # changes the physical retrieval, not the engine or the registry contract.
    label_a, _ = await rel_a.resolver(None, uuid.uuid4(), "ARM0242")
    label_b, _ = await rel_b.resolver(None, uuid.uuid4(), "ARM0242")
    assert label_a == label_b == "Grade 1 A"
    assert calls == ["A", "B"]

    # The engine's derivation helper takes a resolver via the registry — no physical column
    # name appears in the derivation module source (§20).
    src = inspect.getsource(derivation)
    assert "class_id" not in src
    assert "student_enrollment" not in src


def test_registry_edge_is_semantic_not_physical():
    rel = find_relationship("student", "class")
    assert rel is not None
    assert rel.name == "belongs_to"
    # The registry stores the semantic edge + a resolver, never a physical column.
    assert "class_id" not in repr((rel.name, rel.source, rel.target, rel.target_param))


# ── §16 pack never grants authorization (variance is display/business, not access) ──────


def test_attendance_policy_and_grading_are_pure_data():
    for pack in (SCHOOL_A_PACK, SCHOOL_B_PACK, SCHOOL_C_PACK, SCHOOL_MINIMAL_PACK):
        assert isinstance(pack.attendance, AttendancePolicy)
        for value in vars(pack.attendance).values():
            assert not callable(value)


# ── DB-backed §11/§27: same runtime + same records -> different % strictly from the pack ─


@pytest.mark.asyncio
async def test_same_records_different_attendance_result_per_pack(
    test_school: School, test_class: Class, db_session: AsyncSession
):
    """One student's raw rows scored under A/B/C via the SAME capability -> different %."""
    from app.db.models.user import UserRole

    user_row = User(
        school_id=test_school.id, username="var_stu_user", mobile="+919000000001",
        full_name="Variance Student", role=UserRole.STUDENT, is_active=True, password_hash="x",
    )
    db_session.add(user_row)
    await db_session.flush()
    student = Student(
        school_id=test_school.id, user_id=user_row.id, class_id=test_class.id,
        admission_no="VAR001",
    )
    db_session.add(student)
    await db_session.flush()

    # 10 present, 2 late, 2 half_day, 1 absent on distinct dates.
    from datetime import date, timedelta

    day = date(2026, 7, 1)
    plan = (["present"] * 10) + (["late"] * 2) + (["half_day"] * 2) + (["absent"] * 1)
    for i, status in enumerate(plan):
        db_session.add(Attendance(
            school_id=test_school.id, student_id=student.id, class_id=test_class.id,
            date=day + timedelta(days=i), status=AttendanceStatus(status),
            marked_by=user_row.id,
        ))
    await db_session.flush()

    user = _User(test_school.id)

    async def pct_under(pack):
        with use_school_pack(pack):
            block = await student_attendance(db_session, user, {"student": "VAR001"})
        return next(m["value"] for m in block["metrics"] if m["label"] == "Attendance")

    a = await pct_under(SCHOOL_A_PACK)
    b = await pct_under(SCHOOL_B_PACK)
    c = await pct_under(SCHOOL_C_PACK)

    assert a == round(14 / 15 * 100, 1)   # 14/15
    assert b == round(13 / 15 * 100, 1)   # late@0.5 -> 13/15
    assert c == round(12 / 13 * 100, 1)   # half_day excluded -> 12/13
    assert len({a, b, c}) == 3            # three materially different results, same runtime


@pytest.mark.asyncio
async def test_low_attendance_threshold_uses_active_pack_policy(
    test_school: School, test_class: Class, db_session: AsyncSession
):
    """low_attendance_students scores each student under the active pack policy (§4/§11)."""
    from app.db.models.user import UserRole

    u = User(school_id=test_school.id, username="var_low_user", mobile="+919000000002",
             full_name="Low Att Student", role=UserRole.STUDENT, is_active=True, password_hash="x")
    db_session.add(u)
    await db_session.flush()
    s = Student(school_id=test_school.id, user_id=u.id, class_id=test_class.id, admission_no="VAR002")
    db_session.add(s)
    await db_session.flush()

    from datetime import date, timedelta

    day = date(2026, 7, 1)
    # 6 present, 4 late, 0 absent: A -> 100% (late credited); B -> (6+2)/10 = 80%.
    plan = (["present"] * 6) + (["late"] * 4)
    for i, status in enumerate(plan):
        db_session.add(Attendance(
            school_id=test_school.id, student_id=s.id, class_id=test_class.id,
            date=day + timedelta(days=i), status=AttendanceStatus(status),
            marked_by=u.id,
        ))
    await db_session.flush()

    user = _User(test_school.id)

    async def below(pack, threshold):
        with use_school_pack(pack):
            block = await low_attendance_students(db_session, user, {"below_percent": threshold})
        return {r["admission_no"] for r in block.get("rows", [])}

    # Under A the student is at 100% -> not below 90.
    assert "VAR002" not in await below(SCHOOL_A_PACK, 90)
    # Under B the student is at 80% -> below 90.
    assert "VAR002" in await below(SCHOOL_B_PACK, 90)
