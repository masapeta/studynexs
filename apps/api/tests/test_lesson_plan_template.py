"""Template lesson plan structure matches the standard school document."""
from __future__ import annotations

import uuid

from app.core.staff_permissions import StaffScope
from app.db.models.lesson_plan import LessonPlan, LessonPlanStatus
from app.modules.curriculum.services.lesson_plan_pdf import render_lesson_plan_html
from app.modules.curriculum.services.lesson_plan_service import LessonPlanService


def test_template_segments_match_standard_procedure_table():
    segments = LessonPlanService._segments_for_topic("Quadratic Equations")
    assert len(segments) == 6
    assert segments[0]["activity"] == "Introduction"
    assert segments[-1]["activity"] == "Assessment"
    assert all(s.get("description") for s in segments)
    assert all(s.get("notes") for s in segments)
    assert sum(s["duration_min"] for s in segments) == 50


def test_template_objectives_and_materials_are_structured():
    objectives = LessonPlanService._objectives_for_topic("Fractions")
    materials = LessonPlanService._materials_for_topic("Mathematics", "Fractions")
    assert len(objectives) >= 2
    assert "Fractions" in objectives[0]
    assert any("Fractions" in item for item in materials)


def test_lesson_plan_pdf_html_contains_standard_sections():
    html_doc = render_lesson_plan_html(
        teacher_name="Ms. Rao",
        subject_name="Mathematics",
        class_label="Class 8 A",
        scheduled_for=None,
        topic="Quadratic Equations",
        duration_minutes=50,
        learning_objectives=["Understand quadratic forms."],
        materials=["Textbook", "Whiteboard"],
        segments=LessonPlanService._segments_for_topic("Quadratic Equations"),
    )
    assert "SCHOOL LESSON PLAN" in html_doc
    assert "Materials Needed" in html_doc
    assert "Activity/Step" in html_doc
    assert "Introduction" in html_doc


def test_can_view_allows_assigned_teacher():
    cid, sid, author = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    plan = LessonPlan(
        school_id=uuid.uuid4(),
        class_id=cid,
        subject_id=sid,
        created_by=author,
        title="Plan",
        topic="Algebra",
        segments=[],
        status=LessonPlanStatus.APPROVED,
    )
    scope = StaffScope(
        user_id=uuid.uuid4(),
        role="teacher",
        teaching_pairs={(cid, sid)},
        incharge_class_ids=set(),
        is_admin=False,
    )
    assert LessonPlanService(db=None).can_view(scope, plan) is True
