"""Composable multi-capability execution (Phase 4).

A compositional plan is a small, bounded DAG of operations. Each operation either:
  - is a SOURCE that produces a row set keyed by a canonical id (class_id / student_id), or
  - ENRICHES the prior op's rows with an extra column (batched by canonical id — never per-row),
  - or FILTERS the prior op's rows.

Joins are implicit and canonical-id based: an enricher augments the same rows keyed by
class_id/student_id, so we never join on display names. Aggregation for class metrics is
done in SQL (authoritative). The output spec applies sort/limit/projection.

This composes the SAME reusable capabilities — there is no special-purpose "low attendance
+ high fees" tool. The plan describes WHAT; each capability decides HOW (batched SQL).

Bounds (reject beyond these): max operations, single source, batched enrichers only.
Parallelism note: one AsyncSession is not concurrency-safe, and every enricher is a single
batched query, so operations run sequentially by design (fast + safe), not row-by-row.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.academic import Class, Subject, TeacherSubjectMapping
from app.db.models.attendance import Attendance
from app.db.models.examination import Exam, ExamMark
from app.db.models.fee import StudentFeeRecord
from app.db.models.student import Student
from app.db.models.user import User
from app.modules.workspace.assistant.resolver import resolve_class
from app.modules.workspace.assistant.temporal import DateRange

MAX_OPERATIONS = 8

FilterOp = Literal["<", "<=", ">", ">=", "==", "!="]

_SOURCES = {"classes_overview", "class_students", "students_overview"}
_ENRICHERS = {
    "enrich_attendance", "enrich_fees", "enrich_class_teacher", "enrich_exam_average",
}
_ALL_CAPS = _SOURCES | _ENRICHERS | {"filter"}

# Capabilities that reflect only the PRESENT relationship/state (no effective-dated history).
# A PAST temporal token on any of these can't be answered — block, never substitute (P0, §11).
_CURRENT_STATE_CAPS = {
    "classes_overview", "class_students", "students_overview", "enrich_class_teacher",
}

# School-wide student sources can be large; cap the base row set before enrichment.
MAX_SOURCE_ROWS = 2000


class CompositionError(Exception):
    """Raised when a plan is invalid or violates execution bounds."""


@dataclass
class CompFilter:
    field: str
    op: FilterOp
    value: float

    def apply(self, rows: list[dict]) -> list[dict]:
        out = []
        for r in rows:
            v = r.get(self.field)
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if self._cmp(fv):
                out.append(r)
        return out

    def _cmp(self, v: float) -> bool:
        t = self.value
        return {
            "<": v < t, "<=": v <= t, ">": v > t, ">=": v >= t,
            "==": v == t, "!=": v != t,
        }[self.op]


@dataclass
class CompOperation:
    id: str
    capability: str
    depends_on: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)
    filters: list[CompFilter] = field(default_factory=list)


@dataclass
class CompositionPlan:
    operations: list[CompOperation]
    columns: list[str] = field(default_factory=list)
    sort_field: str | None = None
    sort_desc: bool = True
    limit: int | None = None
    output_kind: str = "table"  # "table" | "metrics"


# ── Plan parsing + validation ─────────────────────────────────────────────────


def parse_plan(raw: dict[str, Any]) -> CompositionPlan:
    ops_raw = raw.get("operations") or []
    if not isinstance(ops_raw, list) or not ops_raw:
        raise CompositionError("plan has no operations")
    if len(ops_raw) > MAX_OPERATIONS:
        raise CompositionError(f"too many operations (>{MAX_OPERATIONS})")

    ops: list[CompOperation] = []
    ids: set[str] = set()
    source_count = 0
    for i, o in enumerate(ops_raw):
        cap = o.get("capability")
        if cap not in _ALL_CAPS:
            raise CompositionError(f"unknown capability: {cap}")
        if cap in _SOURCES:
            source_count += 1
        op_id = str(o.get("id") or f"op{i}")
        filters = [
            CompFilter(field=f["field"], op=f["op"], value=float(f["value"]))
            for f in (o.get("filters") or [])
            if f.get("field") and f.get("op") is not None and f.get("value") is not None
        ]
        depends = [str(d) for d in (o.get("depends_on") or [])]
        for d in depends:
            if d not in ids:
                raise CompositionError(f"operation '{op_id}' depends on unknown '{d}'")
        ops.append(
            CompOperation(
                id=op_id, capability=cap, depends_on=depends,
                params=o.get("params") or {}, filters=filters,
            )
        )
        ids.add(op_id)
    if source_count != 1:
        raise CompositionError("plan must have exactly one source operation")
    if ops[0].capability not in _SOURCES:
        raise CompositionError("first operation must be the source")

    output = raw.get("output") or {}
    return CompositionPlan(
        operations=ops,
        columns=[str(c) for c in (output.get("columns") or [])],
        sort_field=output.get("sort_field") or (output.get("sort") or {}).get("field"),
        sort_desc=str((output.get("sort") or {}).get("dir", "desc")).lower() != "asc"
        if output.get("sort") else bool(output.get("sort_desc", True)),
        limit=output.get("limit"),
        output_kind=output.get("type") or output.get("kind") or "table",
    )


# ── Source capabilities (produce rows keyed by a canonical id) ────────────────


async def _classes_overview(
    db: AsyncSession, school_id: uuid.UUID, rng: DateRange | None, params: dict
) -> list[dict]:
    """One row per class: class_id, class_label, student_count, attendance_pct, class_teacher."""
    classes = (
        await db.execute(
            select(Class.id, Class.grade, Class.section, Class.class_incharge_id)
            .where(Class.school_id == school_id)
            .order_by(Class.grade, Class.section)
        )
    ).all()
    if not classes:
        return []
    class_ids = [c.id for c in classes]

    counts = dict(
        (
            await db.execute(
                select(Student.class_id, func.count())
                .where(Student.school_id == school_id, Student.class_id.in_(class_ids))
                .group_by(Student.class_id)
            )
        ).all()
    )

    weight = case(
        (Attendance.status == "half_day", 0.5),
        (Attendance.status == "absent", 0.0),
        else_=1.0,
    )
    att_q = select(Attendance.class_id, func.count(), func.sum(weight)).where(
        Attendance.school_id == school_id, Attendance.class_id.in_(class_ids)
    )
    if rng and not rng.is_all_time:
        if rng.start_date:
            att_q = att_q.where(Attendance.date >= rng.start_date)
        if rng.end_date:
            att_q = att_q.where(Attendance.date < rng.end_date)
    att_rows = (await db.execute(att_q.group_by(Attendance.class_id))).all()
    att_map = {cid: round(float(cr) / n * 100, 1) for cid, n, cr in att_rows if n}

    incharge_ids = [c.class_incharge_id for c in classes if c.class_incharge_id]
    names: dict[uuid.UUID, str] = {}
    if incharge_ids:
        names = dict(
            (
                await db.execute(
                    select(User.id, User.full_name).where(User.id.in_(incharge_ids))
                )
            ).all()
        )

    return [
        {
            "class_id": str(c.id),
            "class_label": f"{c.grade} {c.section}".strip(),
            "student_count": counts.get(c.id, 0),
            "attendance_pct": att_map.get(c.id),
            "class_teacher": names.get(c.class_incharge_id) if c.class_incharge_id else None,
        }
        for c in classes
    ]


async def _class_students(
    db: AsyncSession, school_id: uuid.UUID, params: dict
) -> list[dict]:
    """One row per student in a class: student_id, name, admission_no, class_label."""
    token = str(params.get("class_label") or params.get("class") or "").strip()
    res = await resolve_class(db, school_id, token)
    if res.is_empty:
        raise CompositionError(f"class not found: {token}")
    class_ids = [c.id for c in res.candidates]
    rows = (
        await db.execute(
            select(
                Student.id, User.full_name, Student.admission_no, Class.grade, Class.section
            )
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(Student.school_id == school_id, Student.class_id.in_(class_ids))
            .order_by(Student.admission_no)
        )
    ).all()
    return [
        {
            "student_id": str(sid),
            "name": name,
            "admission_no": adm,
            "class_label": f"{grade} {section}".strip(),
        }
        for sid, name, adm, grade, section in rows
    ]


async def _students_overview(
    db: AsyncSession, school_id: uuid.UUID, params: dict
) -> list[dict]:
    """One row per student across the school: student_id, name, admission_no, class_label.

    Bounded by MAX_SOURCE_ROWS so a fan-out enricher can't explode. Callers that need a
    'top N' usually add enrich_fees + sort + limit downstream.
    """
    rows = (
        await db.execute(
            select(
                Student.id, User.full_name, Student.admission_no, Class.grade, Class.section
            )
            .join(User, User.id == Student.user_id)
            .join(Class, Class.id == Student.class_id)
            .where(Student.school_id == school_id)
            .order_by(Student.admission_no)
            .limit(MAX_SOURCE_ROWS)
        )
    ).all()
    return [
        {
            "student_id": str(sid),
            "name": name,
            "admission_no": adm,
            "class_label": f"{grade} {section}".strip(),
        }
        for sid, name, adm, grade, section in rows
    ]


# ── Enricher capabilities (batched; add a column keyed by canonical id) ───────


async def _enrich_attendance(
    db: AsyncSession, school_id: uuid.UUID, rows: list[dict], rng: DateRange | None
) -> list[dict]:
    ids = [uuid.UUID(r["student_id"]) for r in rows if r.get("student_id")]
    if not ids:
        return rows
    weight = case(
        (Attendance.status == "half_day", 0.5),
        (Attendance.status == "absent", 0.0),
        else_=1.0,
    )
    q = select(Attendance.student_id, func.count(), func.sum(weight)).where(
        Attendance.school_id == school_id, Attendance.student_id.in_(ids)
    )
    if rng and not rng.is_all_time:
        if rng.start_date:
            q = q.where(Attendance.date >= rng.start_date)
        if rng.end_date:
            q = q.where(Attendance.date < rng.end_date)
    pct = {
        str(sid): round(float(cr) / n * 100, 1)
        for sid, n, cr in (await db.execute(q.group_by(Attendance.student_id))).all()
        if n
    }
    for r in rows:
        r["attendance_pct"] = pct.get(r["student_id"])
    return rows


async def _enrich_fees(
    db: AsyncSession, school_id: uuid.UUID, rows: list[dict]
) -> list[dict]:
    ids = [uuid.UUID(r["student_id"]) for r in rows if r.get("student_id")]
    if not ids:
        return rows
    q = (
        select(
            StudentFeeRecord.student_id,
            func.coalesce(func.sum(StudentFeeRecord.amount - StudentFeeRecord.paid_amount), 0),
        )
        .where(StudentFeeRecord.school_id == school_id, StudentFeeRecord.student_id.in_(ids))
        .group_by(StudentFeeRecord.student_id)
    )
    due = {str(sid): float(d) for sid, d in (await db.execute(q)).all()}
    for r in rows:
        r["fee_due"] = due.get(r["student_id"], 0.0)
    return rows


async def _enrich_exam_average(
    db: AsyncSession, school_id: uuid.UUID, rows: list[dict]
) -> list[dict]:
    """Add exam_average (% of total across all recorded marks) per student, batched.

    Overall % = sum(marks_obtained) / sum(total_marks) across the student's marks. This is a
    mark-weighted average of recorded exams — labelled as such; the ERP has no pass mark.
    """
    ids = [uuid.UUID(r["student_id"]) for r in rows if r.get("student_id")]
    if not ids:
        return rows
    q = (
        select(
            ExamMark.student_id,
            func.sum(ExamMark.marks_obtained),
            func.sum(Exam.total_marks),
        )
        .join(Exam, Exam.id == ExamMark.exam_id)
        .where(ExamMark.school_id == school_id, ExamMark.student_id.in_(ids))
        .group_by(ExamMark.student_id)
    )
    avg = {
        str(sid): round(float(obt) / float(tot) * 100, 1)
        for sid, obt, tot in (await db.execute(q)).all()
        if tot
    }
    for r in rows:
        r["exam_average"] = avg.get(r["student_id"])
    return rows


async def _enrich_class_teacher(
    db: AsyncSession, school_id: uuid.UUID, rows: list[dict]
) -> list[dict]:
    """Add subject-teacher names per class (class incharge is already in classes_overview)."""
    ids = [uuid.UUID(r["class_id"]) for r in rows if r.get("class_id")]
    if not ids:
        return rows
    q = (
        select(Class.id, User.full_name, Subject.name)
        .join(TeacherSubjectMapping, TeacherSubjectMapping.class_id == Class.id)
        .join(User, User.id == TeacherSubjectMapping.teacher_id)
        .join(Subject, Subject.id == TeacherSubjectMapping.subject_id)
        .where(TeacherSubjectMapping.school_id == school_id, Class.id.in_(ids))
    )
    by_class: dict[str, list[str]] = {}
    for cid, tname, subject in (await db.execute(q)).all():
        by_class.setdefault(str(cid), []).append(f"{tname} ({subject})")
    for r in rows:
        r["subject_teachers"] = ", ".join(by_class.get(r["class_id"], [])) or "—"
    return rows


# ── Executor ──────────────────────────────────────────────────────────────────


@dataclass
class CompositionResult:
    rows: list[dict]
    columns: list[str]
    output_kind: str
    trace_ops: list[dict]


async def execute_plan(
    db: AsyncSession,
    user: CurrentUser,
    plan: CompositionPlan,
    *,
    resolve_range,
    semantic: str = "NONE",
) -> CompositionResult:
    """Run a validated compositional plan sequentially in dependency order.

    resolve_range: async callable (school_id, token) -> DateRange (injected by the service).
    semantic: the user's SEMANTIC temporality (P0.1). When the request is historically
    PAST, a current-state op must be refused even if the plan dropped that op's time —
    otherwise a composed query could silently join last-month metrics to CURRENT teachers.
    """
    school_id = uuid.UUID(user.school_id)
    outputs: dict[str, list[dict]] = {}
    trace_ops: list[dict] = []
    semantic_past = (semantic or "NONE").strip().upper() == "PAST"

    for op in plan.operations:
        rng: DateRange | None = None
        # Semantic-integrity guard (§5, §12): a PAST request must NOT run a current-state
        # relationship op — even if the plan omitted this op's time (dropped qualifier).
        if semantic_past and op.capability in _CURRENT_STATE_CAPS:
            raise CompositionError(
                "historical_relationship_unavailable: StudyNexs doesn't keep historical "
                f"records for '{op.capability}', so I can't answer that for the requested period."
            )
        if "time" in op.params:
            rng = await resolve_range(school_id, op.params.get("time"))
            # Historical-honesty guard (§11): current-state op + PAST range -> refuse,
            # never present current relationships as the past.
            if rng.is_past and op.capability in _CURRENT_STATE_CAPS:
                raise CompositionError(
                    "historical_relationship_unavailable: StudyNexs doesn't keep historical "
                    f"records for '{op.capability}', so I can't answer that for {rng.label}."
                )

        if op.capability == "classes_overview":
            rows = await _classes_overview(db, school_id, rng, op.params)
        elif op.capability == "class_students":
            rows = await _class_students(db, school_id, op.params)
        elif op.capability == "students_overview":
            rows = await _students_overview(db, school_id, op.params)
        elif op.capability in _ENRICHERS:
            if not op.depends_on:
                raise CompositionError(f"enricher '{op.id}' has no input")
            base = list(outputs[op.depends_on[0]])  # operate on prior rows
            if op.capability == "enrich_attendance":
                rows = await _enrich_attendance(db, school_id, base, rng)
            elif op.capability == "enrich_fees":
                rows = await _enrich_fees(db, school_id, base)
            elif op.capability == "enrich_exam_average":
                rows = await _enrich_exam_average(db, school_id, base)
            else:
                rows = await _enrich_class_teacher(db, school_id, base)
        elif op.capability == "filter":
            if not op.depends_on:
                raise CompositionError(f"filter '{op.id}' has no input")
            rows = list(outputs[op.depends_on[0]])
        else:  # pragma: no cover — guarded by parse_plan
            raise CompositionError(f"unhandled capability: {op.capability}")

        for f in op.filters:
            rows = f.apply(rows)

        outputs[op.id] = rows
        trace_ops.append(
            {
                "id": op.id,
                "capability": op.capability,
                "depends_on": op.depends_on,
                "filters": [{"field": f.field, "op": f.op, "value": f.value} for f in op.filters],
                "row_count": len(rows),
                "time_range": rng.label if rng else None,
            }
        )

    final = outputs[plan.operations[-1].id]

    if plan.sort_field:
        final = sorted(
            final,
            key=lambda r: (r.get(plan.sort_field) is None, r.get(plan.sort_field) or 0),
            reverse=plan.sort_desc,
        )
    if plan.limit:
        final = final[: int(plan.limit)]

    columns = plan.columns or (list(final[0].keys()) if final else [])
    return CompositionResult(final, columns, plan.output_kind, trace_ops)
