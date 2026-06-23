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
