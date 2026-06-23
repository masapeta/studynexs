"""Permissions payload for the authenticated user — drives admin-web nav and actions."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class UserPermissionsOut(BaseModel):
    role: str
    is_admin: bool
    scoped_only: bool
    incharge_class_ids: list[uuid.UUID] = Field(default_factory=list)
    teaching_class_ids: list[uuid.UUID] = Field(default_factory=list)
    # Nav / feature gates
    can_view_dashboard: bool = True
    can_view_classes: bool = False
    can_manage_students: bool = False
    can_manage_staff: bool = False
    can_manage_classes: bool = False
    can_use_ai_papers: bool = False
    can_use_attendance: bool = False
    can_use_exams: bool = False
    can_use_mastery: bool = False
    can_use_report_cards: bool = False
    can_view_timetable: bool = False
    can_edit_timetable: bool = False
    can_use_finance: bool = False
    can_view_notices: bool = True
    can_publish_notices: bool = False
    can_publish_class_notices: bool = False
    can_publish_internal_notices: bool = False
    can_use_settings: bool = False
    can_approve_question_papers: bool = False
