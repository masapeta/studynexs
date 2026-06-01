"""Service-level smoke for the report-card chain (bypasses HTTP/login rate-limit).

Picks a Class 10 student from the demo school, runs the consolidation service end to end
(marks across exams + attendance + a real AI remark), then reloads the persisted row to
prove it saved. Makes one real LLM call.

Run:  python scripts/smoke_report_card.py
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import Class
from app.db.models.report_card import ReportCard
from app.db.models.school import School
from app.db.models.student import Student
from app.db.models.user import User, UserRole
from app.modules.ai.services.report_card_service import generate_report_for_student


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == "test"))
        ).scalar_one()
        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id, User.role == UserRole.SUPER_ADMIN
                )
            )
        ).scalars().first()
        cls = (
            await db.execute(
                select(Class).where(Class.school_id == school.id, Class.grade == "Class 10")
            )
        ).scalars().first()
        student = (
            await db.execute(
                select(Student).where(
                    Student.school_id == school.id, Student.class_id == cls.id
                )
            )
        ).scalars().first()

        print(f">>> school={school.name}  class={cls.grade}-{cls.section}")
        report = await generate_report_for_student(
            db,
            school_id=school.id,
            created_by=principal.id,
            student_id=student.id,
            title="Term Report Card 2026-27",
        )
        await db.commit()

        print(f">>> student={report.student_name}  status={report.status.value}  id={report.id}")
        print(">>> subjects (consolidated across Mid-Term + Final):")
        for s in report.subjects:
            print(f"      {s['subject']:<16} {s['marks_obtained']:>6}/{s['total_marks']}")
        print(f">>> total={report.total_obtained}/{report.total_max}  "
              f"pct={report.percentage}%  grade={report.overall_grade}  "
              f"attendance={report.attendance_percentage}%")
        print(f">>> ai_model={report.ai_model}")
        print(f">>> REMARK: {report.ai_remark}")

        # Reload to prove persistence.
        reloaded = (
            await db.execute(select(ReportCard).where(ReportCard.id == report.id))
        ).scalar_one()
        print(f">>> reloaded from DB OK: {reloaded.student_name} / {reloaded.overall_grade}")


if __name__ == "__main__":
    asyncio.run(main())
