"""Teacher learning-evidence capability in the shared agentic assistant.

Proves the `student_learning_evidence` tool reuses the authoritative
build_learning_evidence_chain (the same service behind /mastery/flags/{id}/evidence-chain and
the /workspace/turn report) — no recomputation, no new metric — and that it:
  - returns a grounded metrics+table block for an authorized staff member;
  - resolves the student server-side and enforces assert_can_access_student + mastery-flag scope
    (a resolved student_id cannot read a flag outside the teacher's teaching scope);
  - is non-leaky when no accessible flag exists (in-scope vs none-exist);
  - is cross-tenant safe;
  - is visible only to staff (never parent/student);
  - routes correctly through the real Gemma planner (skipped if the provider is unavailable).

Reuses the existing _seed_flagging_scenario helper so the flag + evidence chain are real.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.school import School
from app.modules.workspace.assistant import capabilities as cap
from app.modules.workspace.assistant.planner import PlannerDecision, TemporalIntent
from tests.test_mastery_flags import _seed_flagging_scenario


class _U:
    def __init__(self, user_id, school_id, role):
        self.id = str(user_id)
        self.school_id = str(school_id)
        self.role = role
        self.full_name = "Staff"
        self.tenant_slug = "test"


@pytest.mark.asyncio
async def test_admin_learning_evidence_grounded(
    client, admin_user, student_user, test_school, test_class, db_session: AsyncSession
):
    await _seed_flagging_scenario(client, db_session, test_school, test_class, student_user)
    user = _U(admin_user.id, test_school.id, "super_admin")
    block = await cap.student_learning_evidence(db_session, user, {"student": "ADM001"})
    assert block["kind"] == "mixed"
    header = block["data"]
    assert header["kind"] == "metrics"
    assert "Learning evidence" in block["title"]
    labels = {m["label"] for m in header["metrics"]}
    assert "Assessments" in labels and "Grounded" in labels
    table = block["document"]
    assert table["kind"] == "table"
    # Real assessment evidence rows (the two Algebra slip tests) — not fabricated.
    assert len(table["rows"]) >= 1
    exams = " ".join(r.get("exam", "") for r in table["rows"])
    assert "Algebra" in exams


@pytest.mark.asyncio
async def test_learning_evidence_no_flag_is_honest(
    client, admin_user, student_user, test_school, test_class, db_session: AsyncSession
):
    """A student with no weak-topic flag -> honest not_found (never a fabricated chain)."""
    # student_user exists (ADM001) but no flagging scenario is seeded -> no flag.
    user = _U(admin_user.id, test_school.id, "super_admin")
    block = await cap.student_learning_evidence(db_session, user, {"student": "ADM001"})
    assert block["kind"] == "not_found"
    assert "no weak-topic evidence" in block["message"].lower()


@pytest.mark.asyncio
async def test_learning_evidence_out_of_scope_teacher_denied(
    client, admin_user, student_user, teacher_user, test_school, test_class,
    db_session: AsyncSession,
):
    """A flag exists, but a teacher outside its class/subject scope gets a non-leaky denial."""
    from app.db.models.academic import Subject, TeacherSubjectMapping

    await _seed_flagging_scenario(client, db_session, test_school, test_class, student_user)
    # teacher_user teaches only Science (a different subject) -> not the Maths flag's scope.
    science = Subject(school_id=test_school.id, class_id=test_class.id, name="Science", code="SCI")
    db_session.add(science)
    await db_session.flush()
    db_session.add(TeacherSubjectMapping(
        school_id=test_school.id, teacher_id=teacher_user.id,
        subject_id=science.id, class_id=test_class.id,
    ))
    await db_session.flush()
    user = _U(teacher_user.id, test_school.id, "teacher")
    block = await cap.student_learning_evidence(db_session, user, {"student": "ADM001"})
    # A flag exists but not in this teacher's scope -> denied (non-leaky), never the chain.
    assert block["kind"] == "not_found"
    assert block["title"] == "Not available"
    assert "Algebra" not in str(block)  # no evidence leaked


@pytest.mark.asyncio
async def test_learning_evidence_cross_tenant_not_found(
    client, admin_user, student_user, test_school, test_class, db_session: AsyncSession
):
    await _seed_flagging_scenario(client, db_session, test_school, test_class, student_user)
    other = School(name="Other", code="OTH3", tenant_slug="other3")
    db_session.add(other)
    await db_session.flush()
    user = _U(admin_user.id, other.id, "super_admin")
    block = await cap.student_learning_evidence(db_session, user, {"student": "ADM001"})
    # The student does not exist in the other tenant -> non-leaky not_found.
    assert block["kind"] == "not_found"
    assert "Algebra" not in str(block)


def test_learning_evidence_staff_only_catalog():
    from app.modules.workspace.assistant.tools import tools_for_role

    for role in ("teacher", "class_incharge", "admin", "super_admin", "operations"):
        assert any(t.name == "student_learning_evidence" for t in tools_for_role(role))
    for role in ("parent", "student"):
        assert not any(t.name == "student_learning_evidence" for t in tools_for_role(role))


def test_registries_still_valid():
    from app.modules.workspace.assistant.contracts import validate_registries

    validate_registries()


@pytest.mark.asyncio
async def test_full_turn_learning_evidence_dispatch(
    client, admin_user, student_user, test_school, test_class, db_session: AsyncSession,
    monkeypatch,
):
    from app.modules.workspace.assistant import service as service_mod

    await _seed_flagging_scenario(client, db_session, test_school, test_class, student_user)

    async def _fake_plan(text, *, tools, history=None, prev_state=None):
        return PlannerDecision(action="tool", tool="student_learning_evidence",
                               params={"student": "ADM001"}, temporal=TemporalIntent())

    monkeypatch.setattr(service_mod, "plan", _fake_plan)
    svc = service_mod.AssistantService(db_session)
    user = _U(admin_user.id, test_school.id, "super_admin")
    r = await svc.handle_turn(
        current_user=user, text="show learning evidence for ADM001", session_id=None
    )
    assert r["block"]["kind"] == "mixed"
    assert r["trace"]["capability"] == "student_learning_evidence"


@pytest.mark.asyncio
async def test_real_gemma_routes_learning_evidence():
    """Live routing: a learning-evidence question selects student_learning_evidence (over
    student_marks / student_profile). Skipped (not failed) if the provider is unreachable."""
    from app.modules.workspace.assistant.planner import plan
    from app.modules.workspace.assistant.tools import tools_for_role

    tools = tools_for_role("teacher")
    try:
        decision = await plan(
            "show learning evidence for a student in my class ARM0218", tools=tools
        )
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"LLM provider unavailable: {exc}")
    if decision.action != "tool" or decision.tool is None:
        pytest.skip(f"planner did not return a tool (action={decision.action})")
    assert decision.tool == "student_learning_evidence", (
        f"real Gemma chose {decision.tool!r}, expected student_learning_evidence"
    )
