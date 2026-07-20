"""Approved Class 10 Maths CurriculumPack for the Reference School (ARM International School).

Uses Batch 1 architecture: draft pack → chapters/topics/LOs → approve_pack().
Idempotent: skips if approved pack already exists.

Run after seed_reference_school.py (or seed_demo_ssc chain):
  python scripts/seed_reference_school_curriculum.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.db.models.academic import AcademicYear, Class, Subject
from app.db.models.curriculum_pack import CurriculumPack, PackStatus
from app.db.models.school import School
from app.db.models.user import User, UserRole
from app.modules.curriculum.schemas.pack import (
    ChapterIn,
    LearningOutcomeIn,
    PackCreate,
    TopicIn,
)
from app.modules.curriculum.services.pack_service import PackService
from reference_school_config import (
    LOGIN_CLASS_INCHARGE,
    SCHOOL_BOARD,
    TENANT_SLUG,
)

SSC_CLASS10_MATHS: list[tuple[str, str, list[str]]] = [
    ("1", "Real Numbers", ["Euclid's division lemma", "Fundamental theorem of arithmetic"]),
    ("2", "Sets", ["Sets and their representations", "Venn diagrams"]),
    ("3", "Polynomials and Factorisation", ["Zeroes of a polynomial", "Factorisation"]),
    ("4", "Pair of Linear Equations in Two Variables", ["Graphical method", "Substitution"]),
    ("5", "Quadratic Equations", ["Standard form", "Quadratic formula"]),
    ("6", "Progressions", ["Arithmetic progression", "nth term"]),
    ("7", "Coordinate Geometry", ["Distance formula", "Section formula"]),
    ("8", "Similar Triangles", ["Basic proportionality theorem", "Pythagoras theorem"]),
    ("9", "Tangents and Secants to a Circle", ["Tangent properties"]),
    ("10", "Mensuration", ["Surface area and volume"]),
    ("11", "Trigonometry", ["Trigonometric ratios", "Identities"]),
    ("12", "Applications of Trigonometry", ["Angle of elevation and depression"]),
    ("13", "Probability", ["Experimental probability"]),
    ("14", "Statistics", ["Mean, median, mode"]),
]

SSC_BLUEPRINT_80 = [
    {
        "title": "Section I",
        "marks_per_q": 2,
        "count": 6,
        "type": "very_short",
        "instructions": "Answer ALL questions. Each question carries 2 marks.",
    },
    {
        "title": "Section II",
        "marks_per_q": 4,
        "count": 6,
        "type": "short",
        "instructions": "Answer ALL questions. Each question carries 4 marks.",
    },
    {
        "title": "Section III",
        "marks_per_q": 6,
        "count": 6,
        "answer_any": 4,
        "type": "long",
        "instructions": "Answer ANY FOUR of the following six questions. Each carries 6 marks.",
    },
    {
        "title": "Part-B (Objective)",
        "marks_per_q": 1,
        "count": 20,
        "type": "mcq",
        "instructions": "Answer ALL. Each carries 1 mark; write the correct option (A/B/C/D).",
    },
]


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == TENANT_SLUG))
        ).scalar_one_or_none()
        if not school:
            print(f"School not found (tenant_slug='{TENANT_SLUG}'). Run seed_reference_school.py first.")
            return

        cls = (
            await db.execute(
                select(Class).where(
                    Class.school_id == school.id,
                    Class.grade == "Class 10",
                    Class.section == "A",
                )
            )
        ).scalar_one_or_none()
        if not cls:
            print("Class 10-A not found for Reference School.")
            return

        maths = (
            await db.execute(
                select(Subject).where(
                    Subject.school_id == school.id,
                    Subject.class_id == cls.id,
                    Subject.name == "Mathematics",
                )
            )
        ).scalar_one_or_none()
        if not maths:
            print("Mathematics subject not found for Class 10-A.")
            return

        ay = (
            await db.execute(select(AcademicYear).where(AcademicYear.id == cls.academic_year_id))
        ).scalar_one_or_none()
        if not ay:
            print("Academic year not found for Class 10-A.")
            return

        existing = (
            await db.execute(
                select(CurriculumPack).where(
                    CurriculumPack.school_id == school.id,
                    CurriculumPack.class_id == cls.id,
                    CurriculumPack.subject_id == maths.id,
                    CurriculumPack.academic_year_id == ay.id,
                    CurriculumPack.status == PackStatus.APPROVED,
                )
            )
        ).scalars().first()
        if existing:
            print(
                f"Approved CurriculumPack already exists (v{existing.version}, id={existing.id}). "
                "Nothing to do."
            )
            return

        incharge = (
            await db.execute(
                select(User).where(
                    User.school_id == school.id,
                    User.username == LOGIN_CLASS_INCHARGE,
                    User.role == UserRole.CLASS_INCHARGE,
                )
            )
        ).scalar_one_or_none()
        if not incharge:
            incharge = (
                await db.execute(
                    select(User).where(
                        User.school_id == school.id,
                        User.role == UserRole.CLASS_INCHARGE,
                    )
                )
            ).scalars().first()
        if not incharge:
            print("Class incharge user not found.")
            return

        svc = PackService(db)
        pack = await svc.create_pack(
            school.id,
            PackCreate(
                class_id=cls.id,
                subject_id=maths.id,
                academic_year_id=ay.id,
                board=school.board or SCHOOL_BOARD,
                book_title="SSC Mathematics Class 10 (Telangana)",
                publisher="Reference curriculum — SSC board",
                edition="2026-27",
                blueprint=SSC_BLUEPRINT_80,
            ),
            incharge.id,
        )

        for order, (number, title, concepts) in enumerate(SSC_CLASS10_MATHS):
            lo: list[LearningOutcomeIn] = []
            if order == 0:
                lo = [
                    LearningOutcomeIn(
                        code="LO-1",
                        description="Solve linear equations in one variable",
                        order_index=0,
                    )
                ]
            await svc.add_chapter(
                school.id,
                pack.id,
                ChapterIn(
                    number=number,
                    title=title,
                    order_index=order,
                    topics=[
                        TopicIn(
                            title=title,
                            order_index=0,
                            concepts=concepts,
                            learning_outcomes=lo,
                        )
                    ],
                ),
                actor_id=incharge.id,
            )

        approved = await svc.approve_pack(school.id, pack.id, incharge.id)
        await db.commit()
        print(f"Seeded approved CurriculumPack for Reference School ({TENANT_SLUG}) Class 10 Maths")
        print(
            f"  pack_id={approved.id}  version={approved.version}  "
            f"chapters={len(SSC_CLASS10_MATHS)}  blueprint=80 marks SSC"
        )
        print("  Approved via approve_pack() — KG spine + eager RAG indexed.")


if __name__ == "__main__":
    asyncio.run(main())
