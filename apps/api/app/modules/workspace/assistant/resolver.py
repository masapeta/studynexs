"""Entity resolution — turn a natural-language token into canonical ERP entities.

Deterministic first (exact id / normalized name / class label), tenant-scoped by
construction. Returns *candidates* with a confidence label so the caller can ask
a clarifying question when a token is ambiguous (spec §5, §22).

No vector similarity here: ERP entities are identified by exact keys, not meaning.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.school_ops import StaffProfile
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.fees.services.fee_service import _class_label_matches, _normalize_class_label

EntityKind = Literal["student", "teacher", "class"]
MatchStrength = Literal["exact", "strong", "fuzzy"]

_STAFF_ROLES = (
    UserRole.TEACHER,
    UserRole.CLASS_INCHARGE,
    UserRole.ADMIN,
    UserRole.SUPER_ADMIN,
)


@dataclass(frozen=True)
class ResolvedEntity:
    kind: EntityKind
    id: uuid.UUID
    label: str  # human display, e.g. "Aarav Sharma (ARM0218 · Class 2 A)"
    strength: MatchStrength
    detail: dict  # kind-specific extras (admission_no, class_label, role, ...)


@dataclass(frozen=True)
class Resolution:
    """Result of resolving one token to a given entity kind."""

    query: str
    kind: EntityKind
    candidates: list[ResolvedEntity]

    @property
    def is_unique(self) -> bool:
        return len(self.candidates) == 1

    @property
    def is_ambiguous(self) -> bool:
        return len(self.candidates) > 1

    @property
    def is_empty(self) -> bool:
        return not self.candidates

    @property
    def one(self) -> ResolvedEntity | None:
        return self.candidates[0] if self.candidates else None


def _class_label(grade: str, section: str) -> str:
    return f"{grade} {section}".strip()


async def resolve_student(
    db: AsyncSession, school_id: uuid.UUID, token: str, *, limit: int = 6
) -> Resolution:
    """Match a student by admission_no (exact), roll_no (exact), or name (contains)."""
    term = (token or "").strip()
    candidates: list[ResolvedEntity] = []
    if not term:
        return Resolution(query=token, kind="student", candidates=[])

    base = (
        select(Student, User.full_name, Class.grade, Class.section)
        .join(User, User.id == Student.user_id)
        .join(Class, Class.id == Student.class_id)
        .where(Student.school_id == school_id)
    )

    # 1) Exact admission_no / roll_no (case-insensitive) — the strongest signal.
    exact = (
        await db.execute(
            base.where(
                or_(
                    func.lower(Student.admission_no) == term.lower(),
                    func.lower(Student.roll_no) == term.lower(),
                )
            ).limit(limit)
        )
    ).all()
    for student, full_name, grade, section in exact:
        candidates.append(
            ResolvedEntity(
                kind="student",
                id=student.id,
                label=f"{full_name} ({student.admission_no} · {_class_label(grade, section)})",
                strength="exact",
                detail={
                    "name": full_name,
                    "admission_no": student.admission_no,
                    "class_id": str(student.class_id),
                    "class_label": _class_label(grade, section),
                },
            )
        )
    if candidates:
        return Resolution(query=token, kind="student", candidates=candidates)

    # 2) Name contains (fuzzy) — may be ambiguous, caller should clarify.
    like = f"%{term}%"
    named = (
        await db.execute(
            base.where(User.full_name.ilike(like)).order_by(User.full_name).limit(limit)
        )
    ).all()
    for student, full_name, grade, section in named:
        candidates.append(
            ResolvedEntity(
                kind="student",
                id=student.id,
                label=f"{full_name} ({student.admission_no} · {_class_label(grade, section)})",
                strength="strong" if full_name.lower() == term.lower() else "fuzzy",
                detail={
                    "name": full_name,
                    "admission_no": student.admission_no,
                    "class_id": str(student.class_id),
                    "class_label": _class_label(grade, section),
                },
            )
        )
    return Resolution(query=token, kind="student", candidates=candidates)


async def resolve_teacher(
    db: AsyncSession, school_id: uuid.UUID, token: str, *, limit: int = 6
) -> Resolution:
    """Match a staff member by employee_id (exact) or name (contains)."""
    term = (token or "").strip()
    candidates: list[ResolvedEntity] = []
    if not term:
        return Resolution(query=token, kind="teacher", candidates=[])

    # 1) Exact employee_id via StaffProfile.
    emp = (
        await db.execute(
            select(User, StaffProfile.employee_id, StaffProfile.department)
            .join(StaffProfile, StaffProfile.user_id == User.id)
            .where(
                StaffProfile.school_id == school_id,
                func.lower(StaffProfile.employee_id) == term.lower(),
            )
            .limit(limit)
        )
    ).all()
    for user, employee_id, department in emp:
        candidates.append(
            ResolvedEntity(
                kind="teacher",
                id=user.id,
                label=f"{user.full_name} ({employee_id})",
                strength="exact",
                detail={
                    "name": user.full_name,
                    "employee_id": employee_id,
                    "department": department,
                },
            )
        )
    if candidates:
        return Resolution(query=token, kind="teacher", candidates=candidates)

    # 2) Name contains, restricted to staff roles.
    like = f"%{term}%"
    named = (
        await db.execute(
            select(User)
            .where(
                User.school_id == school_id,
                User.role.in_(_STAFF_ROLES),
                User.full_name.ilike(like),
            )
            .order_by(User.full_name)
            .limit(limit)
        )
    ).scalars().all()
    for user in named:
        candidates.append(
            ResolvedEntity(
                kind="teacher",
                id=user.id,
                label=user.full_name,
                strength="strong" if user.full_name.lower() == term.lower() else "fuzzy",
                detail={"name": user.full_name, "role": user.role.value},
            )
        )
    return Resolution(query=token, kind="teacher", candidates=candidates)


async def resolve_class(
    db: AsyncSession, school_id: uuid.UUID, token: str, *, limit: int = 12
) -> Resolution:
    """Match a class by normalized grade+section label ('2A' -> Class 2 A)."""
    wanted = _normalize_class_label(token)
    candidates: list[ResolvedEntity] = []
    if not wanted:
        return Resolution(query=token, kind="class", candidates=[])

    classes = (
        await db.execute(
            select(Class).where(Class.school_id == school_id).order_by(Class.grade, Class.section)
        )
    ).scalars().all()
    for cls in classes:
        label = _class_label(cls.grade, cls.section)
        if not _class_label_matches(label, wanted):
            continue
        candidates.append(
            ResolvedEntity(
                kind="class",
                id=cls.id,
                label=label,
                strength="exact",
                detail={"grade": cls.grade, "section": cls.section, "class_label": label},
            )
        )
        if len(candidates) >= limit:
            break
    return Resolution(query=token, kind="class", candidates=candidates)
