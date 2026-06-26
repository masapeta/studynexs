"""Examination service."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant_scope import TenantScope
from app.db.models.examination import Exam, ExamMark
from app.modules.examinations.schemas.exam import (
    ExamCreate,
    MarkEntry,
    QuestionDef,
    QuestionSchemaSet,
)


class ExamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_exam(self, school_id: uuid.UUID, data: ExamCreate, created_by: uuid.UUID) -> Exam:
        scope = TenantScope(self.db, school_id)
        await scope.school_class(data.class_id)
        await scope.subject_in_class(data.subject_id, data.class_id)
        exam = Exam(
            school_id=school_id,
            class_id=data.class_id,
            subject_id=data.subject_id,
            exam_type=data.exam_type,
            title=data.title,
            total_marks=data.total_marks,
            date=data.exam_date,
            topic=data.topic.strip() if data.topic else None,
            created_by=created_by,
        )
        self.db.add(exam)
        await self.db.flush()
        return exam

    async def list_exams(self, school_id: uuid.UUID, class_id: uuid.UUID | None = None) -> list[Exam]:
        if class_id:
            await TenantScope(self.db, school_id).school_class(class_id)
        query = select(Exam).where(Exam.school_id == school_id)
        if class_id:
            query = query.where(Exam.class_id == class_id)
        result = await self.db.execute(query.order_by(Exam.date.desc()))
        return list(result.scalars().all())

    async def set_question_schema(
        self, school_id: uuid.UUID, exam_id: uuid.UUID, data: QuestionSchemaSet
    ) -> Exam:
        """Define (or replace) the per-question schema — q-no, max marks, topic."""
        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(exam_id)

        questions = data.questions
        if data.source_paper_id:
            questions = await self._questions_from_paper(school_id, data.source_paper_id)
        if not questions:
            raise ValueError("send questions or a source_paper_id")

        nos = [q.no.strip() for q in questions]
        if len(nos) != len(set(nos)):
            raise ValueError("duplicate question numbers in schema")
        total_max = sum(q.max_marks for q in questions)
        # Internal choice ("answer any 4 of 6") legitimately makes Σmax > total_marks,
        # but Σmax below total_marks means questions are missing.
        if total_max < float(exam.total_marks):
            raise ValueError(
                f"question max marks sum to {total_max}, below exam total {exam.total_marks}"
            )

        # Replacing the schema must not orphan recorded per-question marks.
        existing_qnos = {
            qno
            for (qm,) in (
                await self.db.execute(
                    select(ExamMark.question_marks).where(
                        ExamMark.exam_id == exam_id,
                        ExamMark.school_id == school_id,
                        ExamMark.question_marks.is_not(None),
                    )
                )
            ).all()
            for qno in (qm or {})
        }
        missing = existing_qnos - set(nos)
        if missing:
            raise ValueError(
                f"recorded marks exist for questions not in the new schema: {sorted(missing)}"
            )

        exam.question_schema = [
            {
                "no": q.no.strip(),
                "max_marks": q.max_marks,
                "topic": q.topic.strip() if q.topic else None,
            }
            for q in questions
        ]
        if data.source_paper_id:
            exam.source_paper_id = data.source_paper_id
        await self.db.flush()
        return exam

    async def _questions_from_paper(
        self, school_id: uuid.UUID, paper_id: uuid.UUID
    ) -> list[QuestionDef]:
        """Copy question structure from an approved school-scoped AI question paper."""
        from app.db.models.question_paper import PaperStatus, QuestionPaper

        result = await self.db.execute(
            select(QuestionPaper).where(
                QuestionPaper.id == paper_id,
                QuestionPaper.school_id == school_id,
            )
        )
        paper = result.scalar_one_or_none()
        if not paper:
            raise ValueError("question paper not found")
        if paper.status != PaperStatus.APPROVED:
            raise ValueError("only approved question papers can be imported")

        # Per-question topics don't exist on papers; inherit the paper topic when unambiguous.
        single_topic = paper.topics[0] if paper.topics and len(paper.topics) == 1 else None
        questions = [
            QuestionDef(
                no=str(q.get("number")), max_marks=float(q.get("marks", 0)), topic=single_topic
            )
            for section in (paper.sections or [])
            for q in (section.get("questions") or [])
            if q.get("number") and float(q.get("marks", 0)) > 0
        ]
        if not questions:
            raise ValueError("question paper has no usable questions")
        return questions

    async def enter_marks(self, school_id: uuid.UUID, exam_id: uuid.UUID, entries: list[MarkEntry]) -> int:
        scope = TenantScope(self.db, school_id)
        exam = await scope.exam(exam_id)
        by_student = {e.student_id: e for e in entries}
        await scope.students_in_class(exam.class_id, list(by_student))
        if not by_student:
            return 0

        schema = {q["no"]: float(q["max_marks"]) for q in (exam.question_schema or [])}
        for e in by_student.values():
            if e.question_marks is not None:
                if not schema:
                    raise ValueError("exam has no question schema; send marks_obtained only")
                unknown = set(e.question_marks) - set(schema)
                if unknown:
                    raise ValueError(f"unknown question numbers: {sorted(unknown)}")
                for qno, m in e.question_marks.items():
                    if m < 0 or m > schema[qno]:
                        raise ValueError(f"marks for Q{qno} outside 0..{schema[qno]}")
                # Single source of truth: the total is the sum of question marks.
                e.marks_obtained = round(sum(e.question_marks.values()), 2)

        # Data integrity (not a race): reject marks above the exam's max.
        for e in by_student.values():
            if e.marks_obtained > exam.total_marks:
                raise ValueError("marks_obtained exceeds exam total_marks")

        rows = [
            {
                "school_id": school_id, "exam_id": exam_id, "student_id": sid,
                "marks_obtained": e.marks_obtained, "question_marks": e.question_marks,
                "grade_letter": e.grade_letter, "remarks": e.remarks,
            }
            for sid, e in by_student.items()
        ]

        # Single race-safe upsert (no N+1, no check-then-insert race).
        stmt = pg_insert(ExamMark).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_exam_student",
            set_={
                "marks_obtained": stmt.excluded.marks_obtained,
                "question_marks": stmt.excluded.question_marks,
                "grade_letter": stmt.excluded.grade_letter,
                "remarks": stmt.excluded.remarks,
                "updated_at": func.now(),  # Core upsert skips the ORM onupdate
            },
        )
        await self.db.execute(stmt)
        await self.db.flush()

        # Same-transaction outbox event: the worker recomputes the topic-mastery
        # ledger (and, later, notifies parents). No-ops for untagged exams.
        from app.workers.outbox_helper import emit_event

        await emit_event(
            self.db,
            "exam_marks_entered",
            {
                "school_id": str(school_id),
                "exam_id": str(exam_id),
                "class_id": str(exam.class_id),
                "subject_id": str(exam.subject_id),
            },
            target_module="mastery",
        )
        return len(rows)

    async def get_exam_marks(self, school_id: uuid.UUID, exam_id: uuid.UUID) -> list[ExamMark]:
        await TenantScope(self.db, school_id).exam(exam_id)
        result = await self.db.execute(
            select(ExamMark).where(
                ExamMark.exam_id == exam_id,
                ExamMark.school_id == school_id,
            )
        )
        return list(result.scalars().all())

    async def get_gradebook(self, school_id: uuid.UUID, class_id: uuid.UUID) -> dict:
        """Class-wise subject marks matrix for the latest exam per subject."""
        from app.db.models.academic import Subject
        from app.db.models.student import Student
        from app.db.models.user import User

        await TenantScope(self.db, school_id).school_class(class_id)

        student_rows = (
            await self.db.execute(
                select(Student.id, User.full_name)
                .join(User, User.id == Student.user_id)
                .where(Student.school_id == school_id, Student.class_id == class_id)
                .order_by(User.full_name)
            )
        ).all()
        if not student_rows:
            return {"subjects": [], "students": []}

        exams = (
            await self.db.execute(
                select(Exam)
                .where(Exam.school_id == school_id, Exam.class_id == class_id)
                .order_by(Exam.date.desc().nullslast(), Exam.created_at.desc())
            )
        ).scalars().all()
        latest_by_subject: dict[uuid.UUID, Exam] = {}
        for ex in exams:
            if ex.subject_id not in latest_by_subject:
                latest_by_subject[ex.subject_id] = ex
        if not latest_by_subject:
            return {
                "subjects": [],
                "students": [
                    {"student_id": str(sid), "name": name, "marks": {}, "average": None, "grade_letter": None}
                    for sid, name in student_rows
                ],
            }

        subject_ids = list(latest_by_subject.keys())
        subjects = (
            await self.db.execute(
                select(Subject).where(Subject.id.in_(subject_ids)).order_by(Subject.name)
            )
        ).scalars().all()
        subject_map = {s.id: s for s in subjects}
        exam_ids = [e.id for e in latest_by_subject.values()]

        mark_rows = (
            await self.db.execute(
                select(ExamMark.student_id, Exam.subject_id, ExamMark.marks_obtained, Exam.total_marks)
                .join(Exam, Exam.id == ExamMark.exam_id)
                .where(
                    ExamMark.school_id == school_id,
                    ExamMark.exam_id.in_(exam_ids),
                )
            )
        ).all()
        marks_lookup: dict[tuple[uuid.UUID, uuid.UUID], float] = {}
        pct_lookup: dict[tuple[uuid.UUID, uuid.UUID], float] = {}
        for student_id, subject_id, obtained, total in mark_rows:
            marks_lookup[(student_id, subject_id)] = float(obtained)
            if total:
                pct_lookup[(student_id, subject_id)] = float(obtained) / float(total) * 100

        def _letter(pct: float) -> str:
            if pct >= 90:
                return "A+"
            if pct >= 80:
                return "A"
            if pct >= 70:
                return "B"
            if pct >= 60:
                return "C"
            if pct >= 50:
                return "D"
            return "F"

        subject_out = []
        for sid in sorted(subject_ids, key=lambda x: subject_map.get(x).name if subject_map.get(x) else ""):
            sub = subject_map.get(sid)
            if not sub:
                continue
            short = sub.name[:4] if len(sub.name) > 4 else sub.name
            subject_out.append({"id": str(sid), "name": sub.name, "short": short})

        students_out = []
        for student_id, name in student_rows:
            subject_marks: dict[str, float] = {}
            pcts: list[float] = []
            for sid in subject_ids:
                if (student_id, sid) in marks_lookup:
                    val = marks_lookup[(student_id, sid)]
                    subject_marks[str(sid)] = val
                    if (student_id, sid) in pct_lookup:
                        pcts.append(pct_lookup[(student_id, sid)])
            avg = round(sum(pcts) / len(pcts), 1) if pcts else None
            students_out.append({
                "student_id": str(student_id),
                "name": name,
                "marks": subject_marks,
                "average": avg,
                "grade_letter": _letter(avg) if avg is not None else None,
            })

        return {"subjects": subject_out, "students": students_out}
