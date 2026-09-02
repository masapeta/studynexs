"""Reproduce and verify attendance follows a student after a class change."""
from __future__ import annotations

import uuid
from datetime import date

from qa_common import call, env, login, require_write_enabled, sql

require_write_enabled()
tenant = env("QA_TENANT", "sia")
token = login(tenant, env("QA_ADMIN_USERNAME", "sia_vp"), env("QA_ADMIN_PASSWORD"))
att_date = env("QA_ATTENDANCE_DATE", date.today().isoformat())
school_id = sql(f"SELECT id FROM schools WHERE tenant_slug='{tenant}';")

classes = call("GET", "/api/v1/academic/classes", tenant=tenant, token=token).body
classes = classes.get("items") or [] if isinstance(classes, dict) else []
active_year = sql(
    f"SELECT id FROM academic_years WHERE is_active AND school_id='{school_id}';"
)
populated: list[dict] = []
for school_class in classes:
    if school_class.get("academic_year_id") != active_year:
        continue
    roster = call(
        "GET",
        f"/api/v1/academic/classes/{school_class['id']}/roster",
        tenant=tenant,
        token=token,
    )
    if isinstance(roster.body, dict) and roster.body.get("data"):
        populated.append(school_class)
    if len(populated) == 2:
        break
if len(populated) < 2:
    raise SystemExit("Need two populated classes in the active academic year")

old_class, new_class = populated
student = call(
    "GET",
    f"/api/v1/academic/classes/{old_class['id']}/roster",
    tenant=tenant,
    token=token,
).body["data"][0]
student_id = uuid.UUID(student["id"])

try:
    sql(f"DELETE FROM attendance WHERE student_id='{student_id}' AND date='{att_date}';")
    call(
        "POST",
        "/api/v1/attendance/mark",
        tenant=tenant,
        token=token,
        body={
            "class_id": old_class["id"],
            "date": att_date,
            "entries": [{"student_id": str(student_id), "status": "absent"}],
        },
    )
    call(
        "POST",
        f"/api/v1/academic/students/{student_id}/change-class",
        tenant=tenant,
        token=token,
        body={"class_id": new_class["id"], "reason": "QA class-change probe"},
    )
    marked = call(
        "POST",
        "/api/v1/attendance/mark",
        tenant=tenant,
        token=token,
        body={
            "class_id": new_class["id"],
            "date": att_date,
            "entries": [{"student_id": str(student_id), "status": "present"}],
        },
    )
    row = sql(
        f"SELECT class_id || '|' || status FROM attendance "
        f"WHERE student_id='{student_id}' AND date='{att_date}';"
    )
    print(f"receiving class mark: HTTP {marked.status}")
    print(f"attendance row: {row}")
    print(f"expected class: {new_class['id']}")
    if new_class["id"] not in row or "PRESENT" not in row:
        raise SystemExit("FAIL: attendance row stayed on the old class")
    print("PASS: attendance follows the receiving class")
finally:
    sql(f"DELETE FROM attendance WHERE student_id='{student_id}' AND date='{att_date}';")
    restored = call(
        "POST",
        f"/api/v1/academic/students/{student_id}/change-class",
        tenant=tenant,
        token=token,
        body={"class_id": old_class["id"], "reason": "QA class-change cleanup"},
    )
    if restored.status != 200:
        print(f"WARNING: student cleanup failed with HTTP {restored.status}")
