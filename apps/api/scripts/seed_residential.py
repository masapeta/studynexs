"""Seed residential blocks + room allocations; enable the Residential module on the demo
school. Idempotent: skips block creation if any block exists; always ensures the flag.

Run:  python scripts/seed_residential.py
"""
from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.core.database import async_session_factory
from app.db.models.residential import BlockGender, ResidentialBlock, RoomAllocation
from app.db.models.school import School
from app.db.models.student import Student

BLOCKS = [
    {"block_name": "Sarojini Block (Boys)", "block_gender": BlockGender.BOYS,
     "warden_name": "Mr. Anand Rao", "warden_contact": "+919800013001", "total_rooms": 40},
    {"block_name": "Tagore Block (Girls)", "block_gender": BlockGender.GIRLS,
     "warden_name": "Mrs. Kavita Reddy", "warden_contact": "+919800013002", "total_rooms": 40},
]


async def main() -> None:
    async with async_session_factory() as db:
        school = (
            await db.execute(select(School).where(School.tenant_slug == "test"))
        ).scalar_one_or_none()
        if school is None:
            print("Demo school not found. Run seed_demo_ssc.py first.")
            return

        school.enabled_modules = {**(school.enabled_modules or {}), "residential": True}

        existing = await db.scalar(
            select(func.count()).select_from(ResidentialBlock).where(
                ResidentialBlock.school_id == school.id
            )
        )
        if existing:
            await db.commit()
            print(f"Blocks already seeded (count={existing}); ensured Residential module ON.")
            return

        blocks = []
        for bd in BLOCKS:
            b = ResidentialBlock(school_id=school.id, is_active=True, **bd)
            db.add(b)
            blocks.append(b)
        await db.flush()

        students = (
            await db.execute(select(Student).where(Student.school_id == school.id))
        ).scalars().all()
        n = 0
        for i, stu in enumerate(students):
            if i % 5 != 0:  # ~20% are boarders
                continue
            block = blocks[i % len(blocks)]
            room = f"{(i % 40) + 1:03d}"
            db.add(RoomAllocation(
                school_id=school.id, student_id=stu.id, block_id=block.id, room_number=room,
            ))
            n += 1

        await db.commit()
        print(f"Seeded residential: blocks={len(blocks)} allocations={n} (module ON)")


if __name__ == "__main__":
    asyncio.run(main())
