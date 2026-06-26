"""Seed admissions, expenses, and demo payroll data for Greenwood-style admin UI."""
from __future__ import annotations

import asyncio
import uuid
from datetime import date

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.school import School
from app.db.models.school_ops import AdmissionCandidate, AdmissionStage, SchoolExpense
from app.db.models.user import User, UserRole


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == "test").limit(1))
        ).scalar_one_or_none()
        if not school:
            print("School slug=test not found — run main seed first.")
            return

        principal = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id,
                    User.role == UserRole.SUPER_ADMIN,
                ).limit(1)
            )
        ).scalar_one_or_none()
        created_by = principal.id if principal else school.id

        existing = await db.scalar(
            select(AdmissionCandidate.id).where(AdmissionCandidate.school_id == school.id).limit(1)
        )
        if not existing:
            demos = [
                ("Tara Krishnan", "6", AdmissionStage.ENQUIRY, date(2025, 6, 12)),
                ("Dev Malhotra", "7", AdmissionStage.APPLIED, date(2025, 6, 8)),
                ("Sara Pinto", "6", AdmissionStage.INTERVIEW, date(2025, 6, 5)),
                ("Yuvraj Sethi", "7", AdmissionStage.OFFER, date(2025, 5, 28)),
                ("Ira Banerjee", "6", AdmissionStage.APPLIED, date(2025, 6, 10)),
                ("Nikhil Rao", "7", AdmissionStage.ENROLLED, date(2025, 5, 1)),
            ]
            for name, grade, stage, enquiry in demos:
                db.add(
                    AdmissionCandidate(
                        school_id=school.id,
                        name=name,
                        grade_applied=grade,
                        stage=stage,
                        enquiry_date=enquiry,
                        created_by=created_by,
                    )
                )
            print(f"Seeded {len(demos)} admission candidates.")

        exp_exists = await db.scalar(
            select(SchoolExpense.id).where(SchoolExpense.school_id == school.id).limit(1)
        )
        if not exp_exists:
            expenses = [
                ("MSEB", "Utilities", 42000, date(2025, 6, 20)),
                ("Navneet Stationers", "Supplies", 15600, date(2025, 6, 18)),
                ("CoolAir Services", "Maintenance", 8900, date(2025, 6, 15)),
                ("Bharat Petroleum", "Transport", 31200, date(2025, 6, 12)),
            ]
            for vendor, category, amount, exp_date in expenses:
                db.add(
                    SchoolExpense(
                        school_id=school.id,
                        vendor=vendor,
                        category=category,
                        amount=amount,
                        expense_date=exp_date,
                        created_by=created_by,
                    )
                )
            print(f"Seeded {len(expenses)} expenses.")

        await db.commit()
        print("Admin ops demo seed complete.")


if __name__ == "__main__":
    asyncio.run(main())
