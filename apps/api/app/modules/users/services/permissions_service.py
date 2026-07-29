"""Build UserPermissionsOut from StaffScope."""
from __future__ import annotations

from app.core.config import get_settings
from app.core.staff_permissions import StaffScope
from app.modules.users.schemas.permissions import TeachingAssignmentOut, UserPermissionsOut


def portal_permissions(role: str) -> UserPermissionsOut:
    """Minimal gates for parent/student portal shells."""
    is_parent = role == "parent"
    is_student = role == "student"
    return UserPermissionsOut(
        role=role,
        is_admin=False,
        scoped_only=True,
        can_view_dashboard=False,
        can_view_notices=is_parent or is_student,
        can_use_mastery=is_parent or is_student,
    )


def permissions_from_scope(scope: StaffScope) -> UserPermissionsOut:
    has_incharge = bool(scope.incharge_class_ids)
    has_teaching = bool(scope.teaching_pairs)
    is_staff = scope.is_admin or has_incharge or has_teaching or scope.role in (
        "teacher",
        "class_incharge",
        "operations",
    )

    return UserPermissionsOut(
        role=scope.role,
        is_admin=scope.is_admin,
        scoped_only=scope.scoped_only,
        incharge_class_ids=sorted(scope.incharge_class_ids),
        teaching_class_ids=sorted(scope.teaching_class_ids),
        teaching_assignments=[
            TeachingAssignmentOut(class_id=class_id, subject_id=subject_id)
            for class_id, subject_id in sorted(
                scope.teaching_pairs, key=lambda pair: (str(pair[0]), str(pair[1]))
            )
        ],
        can_view_dashboard=True,
        can_view_classes=scope.is_admin or has_incharge,
        can_manage_students=scope.is_admin,
        can_manage_staff=scope.is_admin,
        can_manage_classes=scope.is_admin,
        can_use_ai_papers=scope.is_admin or has_incharge or has_teaching,
        can_use_attendance=scope.is_admin or has_incharge,
        can_use_exams=scope.can_use_exams(),
        can_use_mastery=scope.is_admin or has_incharge or has_teaching,
        can_use_report_cards=scope.is_admin or has_incharge,
        can_view_timetable=is_staff,
        can_edit_timetable=scope.is_admin or has_incharge,
        can_use_finance=scope.is_admin,
        can_view_notices=is_staff,
        can_publish_notices=scope.is_admin,
        can_publish_class_notices=has_incharge,
        can_publish_internal_notices=scope.is_admin,
        can_use_settings=scope.is_admin,
        can_approve_question_papers=scope.is_admin or has_incharge,
        can_generate_ungrounded_question_papers=(
            get_settings().QUESTION_PAPER_UNGROUNDED_ENABLED
            and (scope.is_admin or has_incharge)
        ),
        can_manage_curriculum=scope.is_admin or has_incharge,
        can_edit_curriculum_draft=scope.is_admin or has_incharge or has_teaching,
        can_approve_curriculum=scope.is_admin or has_incharge,
    )
