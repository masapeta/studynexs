"""Batch 3 pilot proof: Principal + Teacher journeys only.

This smoke validates the smallest pilot-success slice:

principal readiness -> teacher scoped curriculum -> grounded lesson plan ->
grounded question paper.

It intentionally does not validate student/parent journeys; those are deferred
unless they block the pilot. It reuses the existing reference tenant,
CurriculumPack, KG/RAG readiness, LLM gateway, and teacher AI endpoints.

Run:
    python scripts/smoke_batch3_principal_teacher_pilot.py
"""
# ruff: noqa: E402,I001
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import httpx

from reference_school_config import (
    DEMO_PASSWORD,
    LOGIN_PRINCIPAL,
    LOGIN_TEACHER_MATHS,
    TENANT_SLUG,
)

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/") or "http://127.0.0.1:8000"
H = {"X-Tenant-Slug": TENANT_SLUG}

results: list[tuple[bool, str, str]] = []


def _data(body: Any) -> Any:
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _list(body: Any) -> list:
    data = _data(body)
    if isinstance(data, list):
        return data
    if isinstance(body, dict):
        return body.get("items") or []
    return []


def _record(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))


def _login(client: httpx.Client, username: str) -> dict[str, str]:
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        headers=H,
        json={"username": username, "password": DEMO_PASSWORD},
    )
    if r.status_code == 429:
        raise RuntimeError(
            f"Login rate-limited for {username!r}; wait or clear scoped login keys."
        )
    r.raise_for_status()
    token = r.json().get("access_token") or (_data(r.json()) or {}).get("access_token")
    if not token:
        raise RuntimeError(f"Login for {username!r} returned no access token")
    return {**H, "Authorization": f"Bearer {token}"}


def _first_quadratic_topic(pack_detail: dict) -> tuple[str, str]:
    chapters = pack_detail.get("chapters") or []
    for chapter in chapters:
        for topic in chapter.get("topics") or []:
            title = topic.get("title") or ""
            if "quadratic" in title.lower():
                return chapter.get("title") or "Quadratic Equations", title
    first_chapter = chapters[0] if chapters else {}
    first_topic = (first_chapter.get("topics") or [{}])[0]
    return (
        first_chapter.get("title") or "Quadratic Equations",
        first_topic.get("title") or "Quadratic Equations",
    )


def _assert_pack_ready(
    client: httpx.Client, auth: dict[str, str], pack_id: str
) -> tuple[bool, dict]:
    r = client.get(
        f"{BASE}/api/v1/curriculum/packs/{pack_id}/intelligence-status",
        headers=auth,
    )
    r.raise_for_status()
    status = _data(r.json()) or {}
    ready = bool(status.get("academic_intelligence_ready"))
    vectors = int(status.get("rag_vector_count") or 0)
    topics = int(status.get("retrievable_topic_count") or 0)
    return ready and vectors > 0 and topics > 0, status


def _class_10a_math(client: httpx.Client, auth: dict[str, str]) -> tuple[dict, dict]:
    classes = client.get(f"{BASE}/api/v1/academic/classes?page_size=100", headers=auth)
    classes.raise_for_status()
    class_items = _list(classes.json())
    cls = next(
        (c for c in class_items if c.get("grade") == "Class 10" and c.get("section") == "A"),
        class_items[0] if class_items else None,
    )
    if not cls:
        raise RuntimeError("No class found for pilot proof")
    subjects = client.get(
        f"{BASE}/api/v1/academic/subjects?class_id={cls['id']}",
        headers=auth,
    )
    subjects.raise_for_status()
    subject_items = _list(subjects.json())
    subject = next(
        (s for s in subject_items if "math" in (s.get("name") or "").lower()),
        subject_items[0] if subject_items else None,
    )
    if not subject:
        raise RuntimeError(f"No subject found for class {cls.get('grade')} {cls.get('section')}")
    return cls, subject


def _approved_math_pack(
    client: httpx.Client,
    auth: dict[str, str],
    *,
    class_id: str | None = None,
    subject_id: str | None = None,
) -> dict:
    r = client.get(f"{BASE}/api/v1/curriculum/packs", headers=auth)
    r.raise_for_status()
    packs = _list(r.json())
    candidates = [
        p
        for p in packs
        if p.get("status") == "approved"
        and (class_id is None or str(p.get("class_id")) == str(class_id))
        and (subject_id is None or str(p.get("subject_id")) == str(subject_id))
    ]
    if not candidates:
        raise RuntimeError("No approved Mathematics CurriculumPack found")
    return candidates[0]


def _question_count(paper: dict) -> tuple[int, int]:
    questions = [
        q
        for section in paper.get("sections") or []
        for q in section.get("questions") or []
    ]
    cited = [q for q in questions if q.get("citations")]
    return len(questions), len(cited)


def main() -> int:
    print(f"Batch 3 Principal + Teacher pilot proof — API {BASE}\n")
    client = httpx.Client(timeout=240.0, follow_redirects=True)

    ready = client.get(f"{BASE}/ready")
    if ready.status_code >= 400:
        print(f"API not ready: {ready.status_code} {ready.text[:300]}")
        return 1
    print(f"/ready: {ready.text}")

    # Principal journey runtime proof.
    principal_auth = _login(client, LOGIN_PRINCIPAL)
    principal_me = client.get(f"{BASE}/api/v1/users/me", headers=principal_auth)
    principal_me.raise_for_status()
    principal = _data(principal_me.json()) or {}
    _record(
        principal.get("username") == LOGIN_PRINCIPAL and principal.get("school_id"),
        "principal login + tenant scope",
        f"role={principal.get('role')} school_id={principal.get('school_id')}",
    )

    perms = client.get(f"{BASE}/api/v1/users/me/permissions", headers=principal_auth)
    perms.raise_for_status()
    principal_perms = _data(perms.json()) or {}
    _record(
        bool(principal_perms.get("can_manage_curriculum")),
        "principal can manage curriculum",
        f"role={principal_perms.get('role')}",
    )
    principal_credits = client.get(f"{BASE}/api/v1/ai/credits", headers=principal_auth)
    principal_credits.raise_for_status()
    principal_credit_data = _data(principal_credits.json()) or {}
    pilot_ai_available = (
        not bool(principal_credit_data.get("at_hard_limit"))
        or bool(principal_credit_data.get("override_active"))
    )
    _record(
        pilot_ai_available,
        "principal AI credits or override available",
        (
            f"remaining={principal_credit_data.get('credits_remaining')} "
            f"hard_limit={principal_credit_data.get('at_hard_limit')} "
            f"override={principal_credit_data.get('override_active')}"
        ),
    )

    classes = client.get(f"{BASE}/api/v1/academic/classes?page_size=100", headers=principal_auth)
    students = client.get(f"{BASE}/api/v1/academic/students?page_size=1", headers=principal_auth)
    dashboard_ok = classes.status_code < 400 and students.status_code < 400
    _record(
        dashboard_ok,
        "principal dashboard data loads",
        f"classes={classes.status_code} students={students.status_code}",
    )

    principal_class, principal_subject = _class_10a_math(client, principal_auth)
    pack = _approved_math_pack(
        client,
        principal_auth,
        class_id=principal_class["id"],
        subject_id=principal_subject["id"],
    )
    pack_id = str(pack["id"])
    pack_ready, pack_status = _assert_pack_ready(client, principal_auth, pack_id)
    _record(
        pack_ready,
        "principal sees Academic Intelligence Ready",
        (
            f"pack={pack_id} vectors={pack_status.get('rag_vector_count')} "
            f"topics={pack_status.get('retrievable_topic_count')}"
        ),
    )
    grounding = client.get(
        f"{BASE}/api/v1/curriculum/packs/{pack_id}/grounding",
        headers=principal_auth,
    )
    grounding.raise_for_status()
    gdata = _data(grounding.json()) or {}
    _record(
        int(gdata.get("source_count") or 0) > 0,
        "principal grounding evidence exists",
        f"source_count={gdata.get('source_count')}",
    )

    # Teacher journey runtime proof.
    teacher_auth = _login(client, LOGIN_TEACHER_MATHS)
    teacher_me = client.get(f"{BASE}/api/v1/users/me", headers=teacher_auth)
    teacher_me.raise_for_status()
    teacher = _data(teacher_me.json()) or {}
    _record(
        teacher.get("username") == LOGIN_TEACHER_MATHS
        and teacher.get("school_id") == principal.get("school_id"),
        "teacher login + same tenant scope",
        f"role={teacher.get('role')} school_id={teacher.get('school_id')}",
    )

    tperms = client.get(f"{BASE}/api/v1/users/me/permissions", headers=teacher_auth)
    tperms.raise_for_status()
    teacher_perms = _data(tperms.json()) or {}
    assignments = teacher_perms.get("teaching_assignments") or []
    assignment_class_ids = {str(a.get("class_id")) for a in assignments if a.get("class_id")}
    _record(
        bool(assignments) and bool(teacher_perms.get("can_use_ai_papers")),
        "teacher assignments + AI permissions",
        (
            f"assignments={len(assignments)} "
            f"can_approve_curriculum={teacher_perms.get('can_approve_curriculum')}"
        ),
    )

    teacher_classes = client.get(
        f"{BASE}/api/v1/academic/classes?page_size=100",
        headers=teacher_auth,
    )
    teacher_classes.raise_for_status()
    visible_classes = _list(teacher_classes.json())
    visible_class_ids = {str(c.get("id")) for c in visible_classes if c.get("id")}
    allowed_class_ids = assignment_class_ids | {
        str(cid) for cid in teacher_perms.get("incharge_class_ids") or []
    }
    unauthorized_visible = sorted(visible_class_ids - allowed_class_ids)
    _record(
        not unauthorized_visible and visible_classes,
        "teacher class scope enforced",
        f"visible={len(visible_classes)} unauthorized={len(unauthorized_visible)}",
    )

    c10, subject = _class_10a_math(client, teacher_auth)
    subject_id = subject.get("id")
    pack = _approved_math_pack(
        client,
        teacher_auth,
        class_id=c10["id"],
        subject_id=subject_id,
    )
    pack_id = str(pack["id"])
    pack_detail = client.get(f"{BASE}/api/v1/curriculum/packs/{pack_id}", headers=teacher_auth)
    pack_detail.raise_for_status()
    chapter, topic = _first_quadratic_topic(_data(pack_detail.json()) or {})
    pack_ready, pack_status = _assert_pack_ready(client, teacher_auth, pack_id)
    _record(
        pack_ready,
        "teacher can access approved ready pack",
        (
            f"class={c10.get('grade')} {c10.get('section')} "
            f"subject={subject.get('name')} pack={pack_id}"
        ),
    )

    lesson = client.post(
        f"{BASE}/api/v1/lesson-plans/generate",
        headers=teacher_auth,
        json={
            "class_id": c10["id"],
            "subject_id": subject_id,
            "pack_id": pack_id,
            "generation_mode": "copilot",
            "topic": topic,
            "chapter": chapter,
        },
    )
    if lesson.status_code >= 400:
        _record(
            False,
            "teacher grounded lesson plan generation",
            f"{lesson.status_code} {lesson.text[:240]}",
        )
    else:
        plan = lesson.json()
        lesson_sources = plan.get("grounding_sources") or []
        _record(
            plan.get("grounded") is True
            and str(plan.get("pack_id")) == pack_id
            and len(lesson_sources) > 0,
            "teacher grounded lesson plan generation",
            f"lesson={plan.get('id')} pack={plan.get('pack_id')} sources={len(lesson_sources)}",
        )

    paper_resp = client.post(
        f"{BASE}/api/v1/ai/question-papers/generate",
        headers=teacher_auth,
        json={
            "class_id": c10["id"],
            "subject_id": subject_id,
            "pack_id": pack_id,
            "topics": [topic],
            "total_marks": 20,
            "duration_minutes": 45,
            "difficulty": "balanced",
            "title": f"Batch 3 Pilot Proof - {topic}",
        },
    )
    if paper_resp.status_code >= 400:
        _record(
            False,
            "teacher grounded question paper generation",
            f"{paper_resp.status_code} {paper_resp.text[:240]}",
        )
    else:
        paper = paper_resp.json()
        questions, cited = _question_count(paper)
        _record(
            paper.get("grounded") is True
            and str(paper.get("pack_id")) == pack_id
            and questions > 0
            and cited > 0,
            "teacher grounded question paper generation",
            (
                f"paper={paper.get('id')} pack={paper.get('pack_id')} "
                f"questions={questions} cited={cited}"
            ),
        )

    print(f"\n{'RES':<4} {'CHECK':<48} DETAIL")
    print("-" * 96)
    fails = 0
    for ok, label, detail in results:
        if not ok:
            fails += 1
        print(f"{'OK' if ok else 'FAIL':<4} {label:<48} {detail}")
    print("-" * 96)
    outcome = "BATCH 3 PRINCIPAL+TEACHER PILOT PROOF: PASS" if fails == 0 else f"{fails} FAILED"
    print(outcome)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
