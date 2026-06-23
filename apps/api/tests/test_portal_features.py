"""Unit tests — product-roadmap teasers are scoped so parents/students never see
staff-only features (the parent-sees-AI-question-papers leak)."""
from __future__ import annotations

from app.modules.portal.services.portal_service import features_for_role

_STAFF_ONLY = {"ai_papers", "answer_eval", "mastery", "report_cards"}


def _ids(role: str) -> set[str]:
    return {f.id for f in features_for_role(role)}


def test_parent_sees_no_staff_features():
    ids = _ids("parent")
    assert ids & _STAFF_ONLY == set(), f"parent leaked staff features: {ids & _STAFF_ONLY}"
    # And no parent-visible teaser links into the staff dashboard.
    for f in features_for_role("parent"):
        assert not (f.href or "").startswith("/dashboard"), f"parent got staff link: {f.href}"


def test_student_sees_no_staff_features():
    ids = _ids("student")
    assert ids & _STAFF_ONLY == set()
    assert "tutor" in ids  # student-relevant feature is present


def test_staff_roles_see_full_roadmap():
    for role in ("teacher", "class_incharge", "admin", "super_admin"):
        ids = _ids(role)
        assert _STAFF_ONLY <= ids, f"{role} missing staff features: {_STAFF_ONLY - ids}"


def test_shared_feature_visible_to_all():
    # WhatsApp alerts are tagged for everyone.
    for role in ("parent", "student", "teacher", "admin"):
        assert "whatsapp" in _ids(role)
