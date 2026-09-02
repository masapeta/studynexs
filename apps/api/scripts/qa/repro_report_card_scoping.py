"""Reproduce report-card period scoping and approval sanity checks.

Checks all three behaviors live through HTTP:
1) Default generation scopes to the student's current academic year.
2) exam_type filter is honored when generating a report card.
3) /approve rejects a persisted impossible report card (defense in depth).

This script creates temporary fixture rows and cleans them up.
"""
from __future__ import annotations

import json
import uuid

from qa_common import call, env, login, require_write_enabled, sql


def _must_dict(label: str, body: object, status: int) -> dict:
    if status != 200 or not isinstance(body, dict):
        raise SystemExit(f"{label} failed: HTTP {status} {body}")
    return body


def _totals(report: dict) -> tuple[float, float, float]:
    return (
        float(report.get("total_obtained") or 0),
        float(report.get("total_max") or 0),
        float(report.get("percentage") or 0),
    )


def _q(value: str) -> str:
    return value.replace("'", "''")


require_write_enabled()
tenant = env("QA_TENANT", "reference")
username = env("QA_USERNAME", "principal")
password = env("QA_PASSWORD", "Demo@1234")
token = login(tenant, username, password)

candidate = sql(
    f"""
    SELECT
      s.id,
      st.id,
      st.class_id,
      c.grade,
      c.section,
      c.academic_year_id,
      (
        SELECT u.id
        FROM users u
        WHERE u.school_id = s.id AND u.role IN ('SUPER_ADMIN', 'ADMIN')
                ORDER BY CASE WHEN u.role = 'SUPER_ADMIN' THEN 0 ELSE 1 END, u.created_at
        LIMIT 1
      ) AS actor_id
    FROM schools s
    JOIN students st ON st.school_id = s.id
    JOIN classes c ON c.id = st.class_id
    WHERE s.tenant_slug = '{_q(tenant)}'
      AND EXISTS (
        SELECT 1
        FROM exam_marks em
        JOIN exams e ON e.id = em.exam_id
        WHERE em.student_id = st.id
          AND em.school_id = s.id
          AND e.class_id = c.id
          AND e.exam_type = 'UNIT_TEST'
          AND em.marks_obtained >= 0
      )
      AND EXISTS (
        SELECT 1
        FROM exam_marks em
        JOIN exams e ON e.id = em.exam_id
        WHERE em.student_id = st.id
          AND em.school_id = s.id
          AND e.class_id = c.id
          AND e.exam_type IN ('MID_TERM', 'FINAL')
          AND em.marks_obtained >= 0
      )
    ORDER BY st.created_at
    LIMIT 1;
    """
)

if not candidate:
    raise SystemExit(
        "No candidate student with unit_test + (mid_term/final) marks found in this tenant"
    )

school_id, student_id, class_id, grade, _, current_year_id, actor_id = candidate.split("|")
if not actor_id:
    raise SystemExit("No admin/super_admin actor found for selected school")

subject_id = sql(
    f"""
    SELECT id
    FROM subjects
    WHERE school_id = '{school_id}' AND class_id = '{class_id}'
    ORDER BY created_at
    LIMIT 1;
    """
)
if not subject_id:
    raise SystemExit("No subject found on selected class")

suffix = str(uuid.uuid4())[:8]
old_year_id = str(uuid.uuid4())
old_class_id = str(uuid.uuid4())
old_subject_id = str(uuid.uuid4())
old_exam_id = str(uuid.uuid4())
old_mark_id = str(uuid.uuid4())
old_attendance_id = str(uuid.uuid4())
bad_report_id = str(uuid.uuid4())

report_ids: list[str] = []

try:
    sql(
        f"""
        INSERT INTO academic_years (id, school_id, year_label, start_date, end_date, is_active)
        VALUES (
          '{old_year_id}',
          '{school_id}',
          'QA-{suffix}-2025',
          DATE '2025-06-01',
          DATE '2026-05-31',
          FALSE
        );
        """
    )
    sql(
        f"""
        INSERT INTO classes (id, school_id, grade, section, academic_year_id)
        VALUES ('{old_class_id}', '{school_id}', '{_q(grade)}', 'Z', '{old_year_id}');
        """
    )
    sql(
        f"""
        INSERT INTO subjects (id, school_id, name, class_id)
        VALUES ('{old_subject_id}', '{school_id}', 'QA Scope Subject {suffix}', '{old_class_id}');
        """
    )
    sql(
        f"""
                INSERT INTO exams (
                    id, school_id, class_id, subject_id, exam_type,
                    title, total_marks, date, created_by
                )
        VALUES (
          '{old_exam_id}',
          '{school_id}',
          '{old_class_id}',
          '{old_subject_id}',
          'FINAL',
          'QA Old-Year Scope {suffix}',
          50.00,
          DATE '2026-03-15',
          '{actor_id}'
        );
        """
    )
    sql(
        f"""
        INSERT INTO exam_marks (id, school_id, exam_id, student_id, marks_obtained, ai_graded)
        VALUES ('{old_mark_id}', '{school_id}', '{old_exam_id}', '{student_id}', 40.00, FALSE);
        """
    )
    sql(
        f"""
        INSERT INTO attendance (id, school_id, student_id, class_id, date, status, marked_by)
        VALUES (
          '{old_attendance_id}',
          '{school_id}',
          '{student_id}',
          '{old_class_id}',
          DATE '2026-03-16',
          'ABSENT',
          '{actor_id}'
        );
        """
    )

    default_resp = call(
        "POST",
        "/api/v1/ai/report-cards/generate",
        tenant=tenant,
        token=token,
        body={"student_id": student_id, "title": f"QA default scope {suffix}"},
        timeout=180,
    )
    default_body = _must_dict("default report", default_resp.body, default_resp.status)
    report_ids.append(str(default_body.get("id")))

    current_resp = call(
        "POST",
        "/api/v1/ai/report-cards/generate",
        tenant=tenant,
        token=token,
        body={
            "student_id": student_id,
            "title": f"QA current year scope {suffix}",
            "academic_year_id": current_year_id,
        },
        timeout=180,
    )
    current_body = _must_dict("current-year report", current_resp.body, current_resp.status)
    report_ids.append(str(current_body.get("id")))

    unit_resp = call(
        "POST",
        "/api/v1/ai/report-cards/generate",
        tenant=tenant,
        token=token,
        body={
            "student_id": student_id,
            "title": f"QA unit-test scope {suffix}",
            "academic_year_id": current_year_id,
            "exam_type": "unit_test",
        },
        timeout=180,
    )
    unit_body = _must_dict("unit-test report", unit_resp.body, unit_resp.status)
    report_ids.append(str(unit_body.get("id")))

    old_resp = call(
        "POST",
        "/api/v1/ai/report-cards/generate",
        tenant=tenant,
        token=token,
        body={
            "student_id": student_id,
            "title": f"QA old-year scope {suffix}",
            "academic_year_id": old_year_id,
        },
        timeout=180,
    )
    old_body = _must_dict("old-year report", old_resp.body, old_resp.status)
    report_ids.append(str(old_body.get("id")))

    default_totals = _totals(default_body)
    current_totals = _totals(current_body)
    unit_totals = _totals(unit_body)
    old_totals = _totals(old_body)

    print(
        "default totals: "
        f"obtained={default_totals[0]:.2f} "
        f"max={default_totals[1]:.2f} "
        f"pct={default_totals[2]:.2f}"
    )
    print(
        "current totals: "
        f"obtained={current_totals[0]:.2f} "
        f"max={current_totals[1]:.2f} "
        f"pct={current_totals[2]:.2f}"
    )
    print(
        "unit_test totals: "
        f"obtained={unit_totals[0]:.2f} "
        f"max={unit_totals[1]:.2f} "
        f"pct={unit_totals[2]:.2f}"
    )
    print(
        "old-year totals: "
        f"obtained={old_totals[0]:.2f} "
        f"max={old_totals[1]:.2f} "
        f"pct={old_totals[2]:.2f}"
    )

    if default_totals != current_totals:
        raise SystemExit(
            "FAIL: default report and explicit current-year report diverged; "
            "default may not be scoping to current year"
        )
    if unit_totals == current_totals:
        raise SystemExit("FAIL: exam_type=unit_test did not change consolidation totals")
    if old_totals[0] != 40.0 or old_totals[1] != 50.0:
        raise SystemExit(
            "FAIL: explicit old-year report did not isolate the seeded old-year exam "
            "(expected 40/50)"
        )

    subjects_json = json.dumps(
        [{"subject": "Maths", "marks_obtained": -100, "total_marks": 20}]
    ).replace("'", "''")
    not_assessed_json = json.dumps([])
    sql(
        f"""
        INSERT INTO report_cards (
          id, school_id, student_id, class_id, created_by, title, student_name, class_name,
          subjects, not_assessed, total_obtained, total_max, percentage, overall_grade, status
        )
        VALUES (
          '{bad_report_id}',
          '{school_id}',
          '{student_id}',
          '{class_id}',
          '{actor_id}',
          'QA invalid legacy card {suffix}',
          'QA Student',
          '{_q(grade)} - A',
          '{subjects_json}'::jsonb,
          '{not_assessed_json}'::jsonb,
          -100,
          20,
          -207.78,
          'E',
                    'DRAFT'
        );
        """
    )

    approve_resp = call(
        "POST",
        f"/api/v1/ai/report-cards/{bad_report_id}/approve",
        tenant=tenant,
        token=token,
        timeout=60,
    )
    print(f"approve invalid legacy card: HTTP {approve_resp.status} -> {approve_resp.body}")
    if approve_resp.status != 422:
        raise SystemExit("FAIL: /approve accepted an impossible persisted report card")

    print("PASS: Phase 3c scoping + approval sanity checks verified live")
finally:
    if report_ids:
        ids = ",".join(f"'{rid}'" for rid in report_ids if rid and rid != "None")
        if ids:
            sql(f"DELETE FROM report_cards WHERE id IN ({ids});")
    sql(f"DELETE FROM report_cards WHERE id = '{bad_report_id}';")
    sql(f"DELETE FROM attendance WHERE id = '{old_attendance_id}';")
    sql(f"DELETE FROM exam_marks WHERE id = '{old_mark_id}';")
    sql(f"DELETE FROM exams WHERE id = '{old_exam_id}';")
    sql(f"DELETE FROM subjects WHERE id = '{old_subject_id}';")
    sql(f"DELETE FROM classes WHERE id = '{old_class_id}';")
    sql(f"DELETE FROM academic_years WHERE id = '{old_year_id}';")
    print("QA fixtures cleaned up")
