"""P1.6 — SchoolPack configuration test.

Proves that school-specific differences (terminology, class-label composition, grading) are
expressed purely through CONFIGURATION (the SchoolPack), while the universal runtime modules
(planner, derivation, conversation, capability contracts, relationship registry) remain
untouched. Also proves the default StudyNexs pack reproduces the reference behaviour exactly.
"""

from __future__ import annotations

import inspect

from app.modules.workspace.assistant.school_pack import (
    SCHOOL_A_PACK,
    SCHOOL_B_PACK,
    SCHOOL_C_PACK,
    GradingScale,
    SchoolPack,
    get_school_pack,
)

# ── The default pack is byte-identical to the pre-P1.6 reference behaviour ──────────────


def test_default_pack_class_label_matches_legacy_format():
    """Legacy formatting was f"{grade} {section}".strip(); the default pack must match it."""
    pack = get_school_pack()
    cases = [("Class 10", "A"), ("Class 9", "B"), ("Class 2", "A"), ("Class 1", "")]
    for grade, section in cases:
        legacy = f"{grade} {section}".strip()
        assert pack.class_label(grade, section) == legacy


def test_default_pack_terminology_unchanged():
    pack = get_school_pack()
    assert pack.slug == "studynexs"
    assert pack.class_incharge_term == "Class Teacher"
    assert pack.teachers_column_label == "Teachers"


def test_default_pack_grading_unchanged():
    pack = get_school_pack()
    assert pack.grade_letter(95) == "A+"
    assert pack.grade_letter(85) == "A"
    assert pack.grade_letter(72) == "B"
    assert pack.grade_letter(61) == "C"
    assert pack.grade_letter(50) == "D"
    assert pack.grade_letter(10) == "F"
    assert pack.grade_letter(None) is None


def test_unknown_or_missing_slug_falls_back_to_default():
    assert get_school_pack(None).slug == "studynexs"
    assert get_school_pack("does-not-exist").slug == "studynexs"


# ── School A/B/C differ purely by configuration ────────────────────────────────────────


def test_school_a_is_parity_with_default():
    """School A configures nothing new -> identical semantics to StudyNexs."""
    default = get_school_pack()
    assert SCHOOL_A_PACK.class_incharge_term == default.class_incharge_term
    assert SCHOOL_A_PACK.class_label("Class 10", "A") == default.class_label("Class 10", "A")
    assert SCHOOL_A_PACK.grade_letter(85) == default.grade_letter(85)


def test_school_b_terminology_and_grading_differ_by_config():
    assert SCHOOL_B_PACK.class_incharge_term == "Form Tutor"
    assert SCHOOL_B_PACK.period_terms["term"] == "Semester"
    # Different grading boundaries -> different letters for the same percentage.
    assert SCHOOL_B_PACK.grade_letter(72) == "A"   # default would be "B"
    assert SCHOOL_B_PACK.grade_letter(56) == "B"
    assert SCHOOL_B_PACK.grade_letter(41) == "C"
    assert SCHOOL_B_PACK.grade_letter(10) == "D"


def test_school_c_class_label_format_differs_by_config():
    assert SCHOOL_C_PACK.class_incharge_term == "Homeroom"
    assert SCHOOL_C_PACK.class_label("Year 2", "A") == "Year 2-A"
    # Same inputs, three schools, three different labels/terms -> configuration, not code.
    assert get_school_pack().class_label("Class 10", "A") == "Class 10 A"
    assert SCHOOL_C_PACK.class_label("Class 10", "A") == "Class 10-A"


def test_all_test_packs_are_the_same_type_and_pure_data():
    """A pack is plain data + pure helpers — never an auth engine, adapter, or callback bag."""
    for pack in (SCHOOL_A_PACK, SCHOOL_B_PACK, SCHOOL_C_PACK):
        assert isinstance(pack, SchoolPack)
        assert isinstance(pack.grading, GradingScale)
        # No field may hold a callable (guards against "bag of arbitrary Python callbacks").
        for value in vars(pack).values():
            assert not callable(value), f"SchoolPack field must be data, got callable: {value!r}"


# ── The universal runtime must NOT depend on any concrete school ────────────────────────


def test_engine_modules_do_not_hardcode_reference_terminology():
    """Planner / derivation / conversation / contracts must not embed school-specific terms."""
    from app.modules.workspace.assistant import (
        contracts,
        conversation,
        derivation,
        planner,
    )

    banned = ("Class Teacher", "Form Tutor", "Homeroom")
    for module in (planner, derivation, conversation, contracts):
        src = inspect.getsource(module)
        for term in banned:
            assert term not in src, f"{module.__name__} hardcodes school term {term!r}"
