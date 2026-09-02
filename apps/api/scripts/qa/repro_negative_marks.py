"""Reproduce negative exam marks and verify the API rejects them."""
from __future__ import annotations

import json
import uuid
from datetime import date

from qa_common import call, env, login, require_write_enabled, sql

require_write_enabled()
tenant = env("QA_TENANT", "sia")
token = login(tenant, env("QA_TEACHER_USERNAME", "teacher6"), env("QA_TEACHER_PASSWORD"))
class_id = env("QA_CLASS_ID")
subject_id = env("QA_SUBJECT_ID")
student_id = env("QA_STUDENT_ID")
academic_year_id = env("QA_ACADEMIC_YEAR_ID")

exam = call(
    "POST",
    "/api/v1/exams",
    tenant=tenant,
    token=token,
    body={
        "title": f"QA negative marks {date.today().isoformat()}",
        "exam_type": "slip_test",
        "class_id": class_id,
        "subject_id": subject_id,
        "academic_year_id": academic_year_id,
        "total_marks": 20,
        "exam_date": date.today().isoformat(),
    },
)
if exam.status not in (200, 201) or not isinstance(exam.body, dict):
    raise SystemExit(f"Exam creation failed: HTTP {exam.status} {exam.body}")
exam_id = (exam.body.get("data") or {}).get("id") or exam.body.get("id")
if not exam_id:
    raise SystemExit(f"Exam response did not contain an id: {exam.body}")

try:
    for marks in (-0.01, -1, -20, -100):
        response = call(
            "POST",
            "/api/v1/exams/marks",
            tenant=tenant,
            token=token,
            body={
                "exam_id": str(uuid.UUID(str(exam_id))),
                "entries": [
                    {"student_id": student_id, "marks_obtained": marks, "remarks": "QA probe"}
                ],
            },
        )
        print(f"marks={marks}: HTTP {response.status} -> {json.dumps(response.body)}")
        if response.status < 400:
            raise SystemExit(f"FAIL: negative marks {marks} were accepted")

    print("PASS: all negative-mark boundaries were rejected")
finally:
    sql(f"DELETE FROM exam_marks WHERE exam_id='{exam_id}';")
    sql(f"DELETE FROM exams WHERE id='{exam_id}';")
    print("QA exam cleaned up")
