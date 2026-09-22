"""P1.7 — cross-school semantic runtime tests.

Proves the SAME semantic runtime behaves correctly under materially different SchoolPack
configurations, changing only the pack — never the planner, conversation, contracts,
derivation, composition, or temporal engine. The structural criteria (§4, §6, §7, §9-§14,
§16, §18, §19, §21, §23) need no DB; the DB-backed section (§17, §22) drives a real
capability under School A/B/C over one seeded tenant and asserts data is identical while only
the display terminology/labels differ, and that isolation holds.
"""

from __future__ import annotations

import inspect
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.school import School
from app.db.models.user import User
from app.modules.workspace.assistant.capabilities import teachers_for_class
from app.modules.workspace.assistant.school_pack import (
    SCHOOL_A_PACK,
    SCHOOL_B_PACK,
    SCHOOL_C_PACK,
    SCHOOL_MINIMAL_PACK,
    GradingScale,
    SchoolPack,
    get_school_pack,
    pack_for_tenant,
    register_tenant_pack,
    use_school_pack,
)

_ALL_TEST_PACKS = (SCHOOL_A_PACK, SCHOOL_B_PACK, SCHOOL_C_PACK)


class _User:
    """Minimal CurrentUser stand-in for direct capability calls."""

    def __init__(self, school_id, role="super_admin", user_id=None, tenant_slug="test"):
        self.school_id = str(school_id)
        self.role = role
        self.id = str(user_id or school_id)
        self.full_name = "Cross-School Admin"
        self.tenant_slug = tenant_slug


# ── §23 blind selection: the active pack comes from the tenant, not the message ─────────


def test_active_pack_defaults_to_studynexs_outside_any_scope():
    assert get_school_pack().slug == "studynexs"


def test_use_school_pack_binds_and_restores():
    assert get_school_pack().slug == "studynexs"
    with use_school_pack(SCHOOL_B_PACK):
        assert get_school_pack().slug == "school_b"
        assert get_school_pack().class_incharge_term == "Form Tutor"
    assert get_school_pack().slug == "studynexs"  # restored


def test_pack_for_tenant_is_blind_and_defaults_safely():
    # Unmapped tenant -> default (real tenants today). No message content involved.
    assert pack_for_tenant("some-real-tenant").slug == "studynexs"
    assert pack_for_tenant(None).slug == "studynexs"
    register_tenant_pack("t_b", "school_b")
    assert pack_for_tenant("t_b").slug == "school_b"
    # An unknown pack slug never leaks another school; it falls back to default.
    register_tenant_pack("t_bad", "does-not-exist")
    assert pack_for_tenant("t_bad").slug == "studynexs"


# ── §7 same intent / different surface: terminology resolves per active pack ─────────────


def test_incharge_terminology_is_per_school():
    assert SCHOOL_A_PACK.class_incharge_term == "Class Teacher"
    assert SCHOOL_B_PACK.class_incharge_term == "Form Tutor"
    assert SCHOOL_C_PACK.class_incharge_term == "Homeroom"


def test_planner_prompt_injects_only_the_active_schools_term():
    """§4/§7: the planner learns THIS school's term from the active pack, not a global list."""
    from app.modules.workspace.assistant.planner import _school_terms

    with use_school_pack(SCHOOL_B_PACK):
        prompt_b = _school_terms()
    with use_school_pack(SCHOOL_C_PACK):
        prompt_c = _school_terms()

    assert "Form Tutor" in prompt_b and "Homeroom" not in prompt_b
    assert "Homeroom" in prompt_c and "Form Tutor" not in prompt_c


# ── §6 class-label semantics: display format is config-driven, identity is not ───────────


def test_class_label_format_is_config_driven():
    assert SCHOOL_A_PACK.class_label("Class 2", "A") == "Class 2 A"
    assert SCHOOL_B_PACK.class_label("Grade 2", "Blue") == "Grade 2 Blue"
    assert SCHOOL_C_PACK.class_label("Year 2", "A") == "Year 2 / Div A"


def test_resolver_display_label_follows_active_pack():
    """resolver._class_label is the single display seam; identity (class id) is unaffected."""
    from app.modules.workspace.assistant.resolver import _class_label

    with use_school_pack(SCHOOL_A_PACK):
        assert _class_label("Class 2", "A") == "Class 2 A"
    with use_school_pack(SCHOOL_C_PACK):
        assert _class_label("Year 2", "A") == "Year 2 / Div A"


# ── §13 academic periods are config-driven ──────────────────────────────────────────────


def test_period_terminology_is_config_driven():
    assert SCHOOL_A_PACK.period_term("term") == "Term"
    assert SCHOOL_B_PACK.period_term("term") == "Semester"
    assert SCHOOL_C_PACK.period_term("term") == "Annual"


# ── §14/§19 grading semantics: config-driven, honest when unconfigured ──────────────────


def test_grading_is_config_driven_per_school():
    # Same 72% -> different representation per school's configured model.
    assert get_school_pack().grade_letter(72) == "B"          # StudyNexs default
    assert SCHOOL_B_PACK.grade_letter(72) == "A"              # 70/55/40/0
    assert SCHOOL_C_PACK.grade_letter(72) == "Merit"         # distinction/merit/pass/fail


def test_missing_grading_configuration_is_honest_not_borrowed():
    """§19: an unconfigured grading model returns nothing — never another school's model."""
    assert SCHOOL_MINIMAL_PACK.supports_grading is False
    assert SCHOOL_MINIMAL_PACK.grade_letter(72) is None
    # It must not silently fall back to the default pack's letters.
    assert SCHOOL_MINIMAL_PACK.grade_letter(95) is None


# ── §9/§10 contracts & relationship registry stay universal (semantic, not physical) ────


def test_capability_contracts_contain_no_school_specific_strings():
    from app.modules.workspace.assistant.contracts import CAPABILITY_CONTRACTS

    banned = ("Class Teacher", "Form Tutor", "Homeroom", "2A", "Grade 2 Blue", "Year 2 / Div")
    for name, contract in CAPABILITY_CONTRACTS.items():
        blob = repr(contract)
        for term in banned:
            assert term not in blob, f"contract {name} contains school-specific {term!r}"


def test_relationship_registry_is_universal():
    from app.modules.workspace.assistant.contracts import RELATIONSHIPS

    banned = ("Class Teacher", "Form Tutor", "Homeroom", "2A", "Grade 2 Blue", "Year 2 / Div")
    for rel in RELATIONSHIPS:
        blob = repr((rel.name, rel.source, rel.target, rel.target_param))
        for term in banned:
            assert term not in blob


# ── §16/§18 configuration isolation: a pack labels; it never grants access ───────────────


def test_pack_admin_roles_are_labelling_only_and_stable():
    """SchoolPack describes role terminology; it does not decide access (§16)."""
    for pack in (get_school_pack(), *_ALL_TEST_PACKS, SCHOOL_MINIMAL_PACK):
        # admin_roles is descriptive metadata, identical across packs unless explicitly set.
        assert pack.admin_roles == frozenset({"admin", "super_admin"})


def test_changing_terminology_does_not_change_contracts_or_relationships():
    """§18: swapping the class-incharge label changes display only — not the contract graph."""
    from app.modules.workspace.assistant.contracts import (
        CAPABILITY_CONTRACTS,
        RELATIONSHIPS,
    )

    before = (repr(sorted(CAPABILITY_CONTRACTS)), repr(RELATIONSHIPS))
    with use_school_pack(SchoolPack(slug="x", class_incharge_term="Guardian")):
        after = (repr(sorted(CAPABILITY_CONTRACTS)), repr(RELATIONSHIPS))
    assert before == after


# ── §21 hard-coding scan: universal modules carry no school-specific strings ─────────────


def test_universal_modules_have_no_school_specific_production_strings():
    from app.modules.workspace.assistant import (
        composition,
        contracts,
        conversation,
        derivation,
        planner,
        resolver,
    )

    banned = ("Class Teacher", "Form Tutor", "Homeroom", "Grade 2 Blue", "Year 2 / Div")
    for module in (planner, conversation, derivation, contracts, composition, resolver):
        src = inspect.getsource(module)
        for term in banned:
            assert term not in src, f"{module.__name__} hardcodes {term!r}"


# ── §11 planner independence: one planner, no per-school branches ────────────────────────


def test_no_per_school_planner_classes_exist():
    from app.modules.workspace.assistant import planner

    src = inspect.getsource(planner)
    for banned in ("SchoolAPlanner", "SchoolBPlanner", "SchoolCPlanner"):
        assert banned not in src


# ── §12 conversation state stores universal meaning, not a school's word ─────────────────


def test_conversation_state_has_no_school_terminology_fields():
    from app.modules.workspace.assistant.conversation import ConversationSemanticState

    fields = ConversationSemanticState.__dataclass_fields__  # type: ignore[attr-defined]
    joined = " ".join(fields).lower()
    for banned in ("form_tutor", "homeroom", "class_teacher"):
        assert banned not in joined


@pytest.mark.parametrize("pack", _ALL_TEST_PACKS)
def test_every_pack_is_pure_data(pack: SchoolPack):
    """A pack never becomes an auth engine, adapter, or callback bag (P1.6 rule, re-checked)."""
    assert isinstance(pack, SchoolPack)
    assert pack.grading is None or isinstance(pack.grading, GradingScale)
    for value in vars(pack).values():
        assert not callable(value), f"SchoolPack field must be data, got callable: {value!r}"


# ── §17/§22 DB-backed: SAME data, SAME capability, only the pack changes the surface ─────


@pytest.mark.asyncio
async def test_same_capability_different_pack_changes_only_surface(
    test_school: School, test_class: Class, teacher_user: User, db_session: AsyncSession
):
    """teachers_for_class over one seeded class returns the SAME teacher under every pack;
    only the class label + incharge role term follow the active SchoolPack (§6, §7)."""
    test_class.class_incharge_id = teacher_user.id  # Grade 1 / A incharge
    await db_session.flush()
    user = _User(test_school.id, user_id=teacher_user.id)

    async def run_under(pack):
        with use_school_pack(pack):
            return await teachers_for_class(db_session, user, {})

    a = await run_under(SCHOOL_A_PACK)
    b = await run_under(SCHOOL_B_PACK)
    c = await run_under(SCHOOL_C_PACK)

    # Same underlying teacher in all three (data is identical; adapter unchanged).
    for block in (a, b, c):
        names = [r["name"] for r in block["rows"]]
        assert teacher_user.full_name in names

    row_a = next(r for r in a["rows"] if r["name"] == teacher_user.full_name)
    row_b = next(r for r in b["rows"] if r["name"] == teacher_user.full_name)
    row_c = next(r for r in c["rows"] if r["name"] == teacher_user.full_name)

    # Role terminology follows the pack.
    assert row_a["role"] == "Class Teacher"
    assert row_b["role"] == "Form Tutor"
    assert row_c["role"] == "Homeroom"

    # Class label format follows the pack (Grade 1 / A).
    assert row_a["class_label"] == "Grade 1 A"
    assert row_b["class_label"] == "Grade 1 A"
    assert row_c["class_label"] == "Grade 1 / Div A"


@pytest.mark.asyncio
async def test_pack_does_not_alter_tenant_isolation(
    test_school: School, test_class: Class, teacher_user: User, db_session: AsyncSession
):
    """§16/§22: a non-default pack never widens data access — a foreign school_id sees nothing."""
    test_class.class_incharge_id = teacher_user.id
    await db_session.flush()

    foreign = _User(uuid.uuid4(), user_id=teacher_user.id)  # different (non-existent) tenant
    with use_school_pack(SCHOOL_B_PACK):
        block = await teachers_for_class(db_session, foreign, {})

    names = [r["name"] for r in block.get("rows", [])]
    assert teacher_user.full_name not in names  # no cross-tenant leak under any pack
