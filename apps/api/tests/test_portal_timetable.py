"""Learner timetable: student sees own class; parent sees linked child's; nobody else's."""
from __future__ import annotations

from datetime import time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.timetable import DayOfWeek, TimetableSlot
from tests.test_exam_result_release import _h, _world


async def _slot(db, fx):
    db.add(TimetableSlot(
        school_id=fx["school"].id, class_id=fx["class"].id, subject_id=fx["subject"].id,
        teacher_id=fx["teacher"].id, day_of_week=DayOfWeek.MONDAY, period_number=1,
        start_time=time(9, 0), end_time=time(9, 45),
    ))
    await db.flush()


@pytest.mark.asyncio
async def test_student_and_parent_read_own_timetable(client: AsyncClient, db_session: AsyncSession):
    fx = await _world(db_session)
    await _slot(db_session, fx)
    r = await client.get("/api/v1/portal/timetable", headers=_h(fx["student_user"]))
    assert r.status_code == 200, r.text
    rows = r.json()["data"]
    assert len(rows) == 1 and rows[0]["subject_name"] == fx["subject"].name
    r = await client.get(f"/api/v1/portal/child/{fx['student'].id}/timetable",
                         headers=_h(fx["parent_user"]))
    assert r.status_code == 200 and len(r.json()["data"]) == 1


@pytest.mark.asyncio
async def test_timetable_ownership(client: AsyncClient, db_session: AsyncSession):
    fx = await _world(db_session)
    await _slot(db_session, fx)
    r = await client.get(f"/api/v1/portal/child/{fx['student2'].id}/timetable",
                         headers=_h(fx["parent_user"]))
    assert r.status_code == 403
    r = await client.get(f"/api/v1/portal/child/{fx['student'].id}/timetable",
                         headers=_h(fx["student_user"]))
    assert r.status_code == 403
    r = await client.get("/api/v1/portal/timetable", headers=_h(fx["incharge"]))
    assert r.status_code == 403
