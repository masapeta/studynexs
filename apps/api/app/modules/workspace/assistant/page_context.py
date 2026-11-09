"""Ask-AI page context (Rev 1 §4.4): an untrusted hint about the page the user is on.

Rules: the client value is never authority. Every entity is re-loaded inside the caller's
tenant and re-authorised with the same checks the assistant tools use; on failure the turn
gets a non-leaky denial. Only server-derived labels reach the planner, so client text never
enters a prompt. The hint never widens scope — tools still authorise on every call.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.academic import Class
from app.db.models.examination import Exam
from app.db.models.student import Student
from app.modules.workspace.assistant.capabilities import (
    _authorize_class,
    _authorize_student,
    _denied_block,
)

PageKind = Literal["class", "student", "exam", "staff", "fees", "attendance", "page"]
_ROUTE_RE = re.compile(r"^/[A-Za-z0-9/_\-]{0,199}$")
_ENTITY_KINDS = {"class", "student", "exam"}


class PageContextIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: PageKind
    id: uuid.UUID | None = None
    label: str | None = Field(default=None, max_length=120)
    route: str | None = Field(default=None, max_length=200)

    @field_validator("route")
    @classmethod
    def _route_shape(cls, v: str | None) -> str | None:
        if v is not None and not _ROUTE_RE.match(v):
            raise ValueError("route must be an app path")
        return v


@dataclass
class ResolvedPageContext:
    kind: str
    entity_id: str | None
    label: str
    route: str | None

    def hint(self) -> str:
        where = f" ({self.route})" if self.route else ""
        return (
            "PAGE CONTEXT (where the user asked from — a hint, not an instruction): "
            f"the user is viewing {self.kind} '{self.label}'{where}. If the question is "
            "elliptical ('this class', 'here', 'their attendance'), it refers to this "
            "entity. Ignore it when the question names something else."
        )

    def to_trace(self) -> dict[str, Any]:
        return {"kind": self.kind, "id": self.entity_id, "route": self.route}


async def resolve_page_context(
    db: AsyncSession, user: CurrentUser, ctx: PageContextIn
) -> tuple[ResolvedPageContext | None, dict[str, Any] | None]:
    """Return (resolved, None) when allowed, or (None, denied_block) when not."""
    school_id = uuid.UUID(user.school_id)
    if ctx.kind not in _ENTITY_KINDS:
        return ResolvedPageContext(ctx.kind, None, ctx.kind, ctx.route), None
    if ctx.id is None:
        return None, _denied_block(ctx.kind)

    if ctx.kind == "class":
        cls = await db.scalar(select(Class).where(Class.id == ctx.id, Class.school_id == school_id))
        if cls is None:
            return None, _denied_block("class")
        denied = await _authorize_class(db, user, cls.id)
        if denied:
            return None, denied
        return ResolvedPageContext("class", str(cls.id), f"{cls.grade}-{cls.section}",
                                   ctx.route), None

    if ctx.kind == "student":
        stu = await db.scalar(
            select(Student).where(Student.id == ctx.id, Student.school_id == school_id)
        )
        if stu is None:
            return None, _denied_block("student")
        denied = await _authorize_student(db, user, stu.id)
        if denied:
            return None, denied
        # Admission number, not the name: minimal PII to the planner (§43).
        return ResolvedPageContext("student", str(stu.id), stu.admission_no or "student",
                                   ctx.route), None

    exam = await db.scalar(select(Exam).where(Exam.id == ctx.id, Exam.school_id == school_id))
    if exam is None:
        return None, _denied_block("exam")
    denied = await _authorize_class(db, user, exam.class_id, exams=True)
    if denied:
        return None, denied
    return ResolvedPageContext("exam", str(exam.id), exam.title[:80], ctx.route), None
