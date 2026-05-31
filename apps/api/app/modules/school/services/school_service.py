"""School profile + academic-year operations (school-scoped)."""
from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import AcademicYear
from app.db.models.school import School
from app.modules.school.schemas.school import AcademicYearCreate, SchoolProfileUpdate


class SchoolService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, school_id: uuid.UUID) -> School:
        return (
            await self.db.execute(select(School).where(School.id == school_id))
        ).scalar_one()

    async def update_profile(self, school_id: uuid.UUID, data: SchoolProfileUpdate) -> School:
        school = await self.get_profile(school_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(school, field, value)
        await self.db.flush()
        return school

    async def list_years(self, school_id: uuid.UUID) -> list[AcademicYear]:
        rows = await self.db.execute(
            select(AcademicYear)
            .where(AcademicYear.school_id == school_id)
            .order_by(AcademicYear.start_date.desc())
        )
        return list(rows.scalars().all())

    async def create_year(self, school_id: uuid.UUID, data: AcademicYearCreate) -> AcademicYear:
        # Only one active year at a time.
        if data.is_active:
            await self.db.execute(
                update(AcademicYear)
                .where(AcademicYear.school_id == school_id)
                .values(is_active=False)
            )
        year = AcademicYear(school_id=school_id, **data.model_dump())
        self.db.add(year)
        await self.db.flush()
        return year
