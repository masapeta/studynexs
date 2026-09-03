import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.academic import Class
from app.db.models.student import Student
from app.db.models.user import User
from tests.conftest import auth_headers, get_auth_token


@pytest.mark.asyncio
async def test_mark_attendance_flow(client: AsyncClient, admin_user: User, student_user: User, test_class: Class, db_session: AsyncSession):
    token = await get_auth_token(client, "test_admin", "Admin@123")
    headers = auth_headers(token)

    # Get student record
    res = await db_session.execute(select(Student).where(Student.user_id == student_user.id))
    student = res.scalar_one()

    # 1. Mark attendance
    mark_data = {
        "class_id": str(test_class.id),
        "date": "2026-07-01",
        "entries": [
            {"student_id": str(student.id), "status": "present", "remarks": "On time"}
        ]
    }
    resp = await client.post("/api/v1/attendance/mark", json=mark_data, headers=headers)
    assert resp.status_code == 200
    assert "Attendance marked" in resp.json()["message"]

    # 2. Get class attendance
    resp = await client.get(f"/api/v1/attendance/class/{test_class.id}?date=2026-07-01", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["status"] == "present"

    # 3. Get summary
    resp = await client.get(f"/api/v1/attendance/class/{test_class.id}/summary?date=2026-07-01", headers=headers)
    assert resp.status_code == 200
    summary = resp.json()["data"]
    assert summary["present"] == 1
    assert summary["absent"] == 0
