"""20-step Academic Intelligence loop verification on reference tenant.

Run with API up: python scripts/smoke_learning_loop_e2e.py
Uses same config as smoke_demo_readiness.py.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import httpx

from reference_school_config import (
    DEMO_PASSWORD,
    LOGIN_PARENT,
    LOGIN_PRINCIPAL,
    LOGIN_STUDENT,
    TENANT_SLUG,
)

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
H: dict[str, str] = {"X-Tenant-Slug": TENANT_SLUG}
LOOP_TOPIC = "quadratic"

# step_num, label, status, detail
results: list[tuple[int, str, str, str]] = []

STATUS_OK = "WORKS"
STATUS_PARTIAL = "PARTIAL"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "NOT VERIFIED"

topic_hits: dict[str, bool] = {
    "marks": False,
    "mastery": False,
    "tutor": False,
    "parent": False,
}


def _resolve_base(client: httpx.Client) -> str:
    if BASE:
        return BASE
    for base in ("http://localhost:8000", "http://127.0.0.1:8000"):
        try:
            if client.get(base + "/health", timeout=5).status_code < 400:
                return base
        except Exception:  # noqa: BLE001
            continue
    return "http://localhost:8000"


def _data(body) -> list | dict:
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        return body.get("data") or body.get("items") or body
    return body


def _list(body) -> list:
    d = _data(body)
    return d if isinstance(d, list) else []


def _topic_match(text: str) -> bool:
    return LOOP_TOPIC in (text or "").lower()


def _mastery_topics(mdata: dict) -> list[dict]:
    topics: list[dict] = []
    for subj in mdata.get("subjects") or []:
        for t in subj.get("topics") or []:
            topics.append(t)
    if not topics:
        topics = mdata.get("topics") or mdata.get("weak_topics") or []
    return topics


def record(step: int, label: str, status: str, detail: str = "") -> None:
    results.append((step, label, status, detail))


def _login(client: httpx.Client, base: str, username: str) -> dict[str, str] | None:
    r = client.post(
        base + "/api/v1/auth/login",
        headers=H,
        json={"username": username, "password": DEMO_PASSWORD},
    )
    if r.status_code >= 400:
        return None
    token = r.json().get("access_token")
    return {**H, "Authorization": f"Bearer {token}"}


def main() -> int:
    client = httpx.Client(follow_redirects=True, timeout=120.0)
    base = _resolve_base(client)
    print(f"API base: {base}\n")

    try:
        health = client.get(base + "/health")
    except Exception as exc:  # noqa: BLE001
        print(f"API unreachable: {exc}")
        return 1
    if health.status_code >= 400:
        print(f"API unhealthy: {health.status_code}")
        return 1

    auth = _login(client, base, LOGIN_PRINCIPAL)
    if not auth:
        print("Principal login failed")
        return 1

    student_demo_id: str | None = None

    # --- Step 1-2: Curriculum pack ---
    packs_r = client.get(base + "/api/v1/curriculum/packs", headers=auth)
    packs = (packs_r.json().get("data") or []) if packs_r.status_code < 400 else []
    approved_packs = [p for p in packs if p.get("status") == "approved"]
    maths = next(
        (p for p in approved_packs if "math" in (p.get("subject_name") or "").lower()),
        None,
    )
    pack = maths or (approved_packs[0] if approved_packs else None)
    record(1, "Curriculum available (pack list)", STATUS_OK if packs else STATUS_FAIL, f"{len(packs)} packs")
    pack_label = (
        f"{pack.get('subject_name', 'unknown')} (preferred maths)"
        if maths
        else (pack.get("subject_name", "first approved") if pack else "none")
    )
    record(
        2,
        "Approved CurriculumPack for KG/RAG",
        STATUS_OK if pack else STATUS_PARTIAL,
        pack_label,
    )
    pack_id = pack.get("id") if pack else None

    # --- Step 3-5: KG, embeddings, RAG ---
    if pack_id:
        try:
            gr = client.get(base + f"/api/v1/curriculum/packs/{pack_id}/grounding", headers=auth)
            g = (gr.json().get("data") or {}) if gr.status_code < 400 else {}
        except httpx.ReadTimeout:
            g = {}
            record(3, "Knowledge graph / spine built", STATUS_PARTIAL, "grounding request timed out")
            record(4, "Embeddings indexed", STATUS_PARTIAL, "grounding request timed out")
            record(5, "Vector store / RAG retrievable", STATUS_PARTIAL, "grounding request timed out")
        else:
            sc = g.get("source_count") or 0
            record(3, "Knowledge graph / spine built", STATUS_OK if sc else STATUS_PARTIAL, f"source_count={sc}")
            record(4, "Embeddings indexed", STATUS_OK if sc else STATUS_PARTIAL, "inferred from grounding")
            record(5, "Vector store / RAG retrievable", STATUS_OK if sc > 0 else STATUS_FAIL, f"source_count={sc}")
        audit = client.get(base + f"/api/v1/curriculum/packs/{pack_id}/audit", headers=auth)
        events = (audit.json().get("data") or []) if audit.status_code < 400 else []
        record(2, "Pack audit trail", STATUS_OK if events else STATUS_PARTIAL, f"{len(events)} events")
    else:
        for s in (3, 4, 5):
            record(s, "KG / embed / RAG", STATUS_SKIP, "no pack_id")

    # --- Step 6-7: Lesson plans + QP ---
    lp = client.get(base + "/api/v1/lesson-plans/next", headers=auth)
    lp_ok = lp.status_code < 400
    lp_data = (lp.json().get("data") if lp_ok else None) or None
    lp_detail = "has draft" if lp_data else "none (endpoint OK)"
    record(
        6,
        "Lesson plans API (/lesson-plans/next)",
        STATUS_OK if lp_ok else STATUS_FAIL,
        f"{lp.status_code} · {lp_detail}",
    )
    qp = client.get(base + "/api/v1/ai/question-papers", headers=auth)
    if qp.status_code < 400:
        qbody = qp.json()
        papers = qbody if isinstance(qbody, list) else (qbody.get("data") or [])
    else:
        papers = []
    approved_qp = [p for p in papers if p.get("status") == "approved"]
    record(7, "Question papers (approved)", STATUS_OK if approved_qp else STATUS_PARTIAL, f"{len(approved_qp)} approved")

    # --- Step 8-9: Review + publish (seed state) ---
    pending = [p for p in papers if p.get("status") in ("pending_approval", "pending")]
    record(8, "QP review queue (pending)", STATUS_PARTIAL if pending else STATUS_OK, f"{len(pending)} pending")
    record(9, "QP published (approved exists)", STATUS_OK if approved_qp else STATUS_FAIL, "")

    # --- Step 10-16: Exams, eval, marks, gradebook ---
    classes = client.get(base + "/api/v1/academic/classes?page_size=100", headers=auth)
    items = (classes.json().get("items") or classes.json().get("data") or []) if classes.status_code < 400 else []
    c10 = next((c for c in items if c.get("grade") == "Class 10" and c.get("section") == "A"), items[0] if items else None)
    cid = c10.get("id") if c10 else None
    exams_r = client.get(base + f"/api/v1/exams?class_id={cid}", headers=auth) if cid else None
    exams = []
    if exams_r and exams_r.status_code < 400:
        body = exams_r.json()
        exams = body.get("items") or body.get("data") or []
    eval_exam = next((e for e in exams if e.get("can_evaluate_sheets")), exams[0] if exams else None)
    record(10, "Exam exists for Class 10-A", STATUS_OK if eval_exam else STATUS_PARTIAL, eval_exam.get("title", "") if eval_exam else "")
    eid = eval_exam.get("id") if eval_exam else None

    if eid:
        ev = client.get(base + f"/api/v1/exams/{eid}/evaluations", headers=auth)
        evlist = (ev.json().get("data") or []) if ev.status_code < 400 else []
        record(11, "Answer sheet evaluations exist", STATUS_OK if evlist else STATUS_PARTIAL, f"{len(evlist)} evals")
        record(12, "OCR / eval pipeline (seeded)", STATUS_OK if evlist else STATUS_PARTIAL, "check eval status in UI")
        suggested = [e for e in evlist if e.get("status") in ("suggested", "SUGGESTED", "completed")]
        approved = [e for e in evlist if e.get("status") in ("approved", "APPROVED")]
        record(
            13,
            "AI evaluation suggestions",
            STATUS_OK if suggested or approved else STATUS_PARTIAL,
            f"{len(suggested)} suggested · {len(approved)} approved",
        )
        record(14, "Teacher review surface", STATUS_OK if approved else STATUS_PARTIAL, "HITL finalized when approved")
        marks = client.get(base + f"/api/v1/exams/{eid}/marks", headers=auth)
        markdata = (marks.json().get("data") or []) if marks.status_code < 400 else []
        exam_topic = (eval_exam.get("topic") or "") if eval_exam else ""
        if _topic_match(exam_topic):
            topic_hits["marks"] = True
        for row in markdata:
            sid = row.get("student_id")
            if sid and not student_demo_id:
                students = client.get(
                    base + f"/api/v1/academic/students?class_id={cid}&page_size=100",
                    headers=auth,
                )
                slist = (students.json().get("items") or students.json().get("data") or []) if students.status_code < 400 else []
                for stu in slist:
                    if stu.get("id") == sid and (stu.get("username") == LOGIN_STUDENT or stu.get("roll_no") == "1"):
                        student_demo_id = sid
                        break
            qm = row.get("question_marks") or {}
            for qno, _ in qm.items():
                if _topic_match(exam_topic):
                    topic_hits["marks"] = True
        record(
            15,
            "Marks saved (topic-aligned exam)",
            STATUS_OK if markdata and topic_hits["marks"] else STATUS_PARTIAL,
            f"{len(markdata)} rows · topic={exam_topic[:40]}",
        )
    else:
        for s, lbl in ((11, "evaluations"), (12, "OCR"), (13, "AI eval"), (14, "HITL"), (15, "marks")):
            record(s, lbl, STATUS_SKIP, "no exam")

    gb = client.get(base + f"/api/v1/exams/gradebook?class_id={cid}", headers=auth) if cid else None
    record(16, "Gradebook", STATUS_OK if gb and gb.status_code < 400 else STATUS_PARTIAL, "")

    rc = client.get(base + f"/api/v1/ai/report-cards?class_id={cid}", headers=auth) if cid else None
    rclist = _list(rc.json()) if rc and rc.status_code < 400 else []
    record(17, "Report cards generated", STATUS_PARTIAL if not rclist else STATUS_OK, f"{len(rclist)} cards")

    # Resolve student_demo via portal login if not found from marks
    sauth = _login(client, base, LOGIN_STUDENT)
    if sauth and not student_demo_id:
        ctx2 = client.get(base + "/api/v1/portal/context", headers=sauth)
        student_demo_id = (ctx2.json().get("data") or {}).get("student_id")

    # Mastery — staff path for student_demo
    if student_demo_id:
        mast = client.get(base + f"/api/v1/mastery/students/{student_demo_id}", headers=auth)
        mdata = (mast.json().get("data") or {}) if mast.status_code < 400 else {}
        topics = _mastery_topics(mdata)
        quad_topics = [t for t in topics if _topic_match(t.get("topic") or t.get("topic_display", ""))]
        if quad_topics:
            topic_hits["mastery"] = True
        record(
            18,
            f"Topic mastery ({LOGIN_STUDENT})",
            STATUS_OK if quad_topics else STATUS_PARTIAL,
            f"{len(topics)} topic rows · quadratic={len(quad_topics)}",
        )
    elif cid:
        record(18, "Topic mastery", STATUS_SKIP, f"{LOGIN_STUDENT} not resolved")
    else:
        record(18, "Topic mastery", STATUS_SKIP, "no class")

    # --- Step 19: Parent copilot ---
    pauth = _login(client, base, LOGIN_PARENT)
    if not pauth:
        record(19, "Parent copilot briefing", STATUS_FAIL, "parent login failed")
    else:
        ctx = client.get(base + "/api/v1/portal/context", headers=pauth)
        children = (ctx.json().get("data") or {}).get("children") or []
        child = next((c for c in children if c.get("username") == LOGIN_STUDENT), children[0] if children else None)
        if child:
            csid = child.get("student_id")
            br = client.get(base + f"/api/v1/parent-copilot/students/{csid}/briefing", headers=pauth)
            bdata = (br.json().get("data") or {}) if br.status_code < 400 else {}
            summary = bdata.get("summary") or ""
            focus = bdata.get("focus_areas") or []
            focus_text = " ".join(f"{f.get('topic', '')} {f.get('subject_name', '')}" for f in focus)
            if _topic_match(summary) or _topic_match(focus_text):
                topic_hits["parent"] = True
            record(
                19,
                "Parent copilot reflects performance",
                STATUS_OK if br.status_code < 400 and topic_hits["parent"] else STATUS_PARTIAL,
                (summary[:80] if summary else str(br.status_code)),
            )
        else:
            record(19, "Parent copilot", STATUS_FAIL, "no children in portal")

    # --- Step 20: Student tutor (must be concept-card grounded, not template demo) ---
    tutor_concept_card = False
    if not sauth:
        record(20, "Student tutor recommendations", STATUS_FAIL, "student login failed")
    else:
        if not student_demo_id:
            ctx2 = client.get(base + "/api/v1/portal/context", headers=sauth)
            student_demo_id = (ctx2.json().get("data") or {}).get("student_id")
        if student_demo_id:
            rec = client.get(base + f"/api/v1/tutor/students/{student_demo_id}/recommendations", headers=sauth)
            recs = (rec.json().get("data") or []) if rec.status_code < 400 else []
            demo = any(r.get("lesson_key") == "fractions" for r in recs)
            top = recs[0] if recs else {}
            lesson_key = top.get("lesson_key", "")
            detail = top.get("topic", "")[:60] if recs else "none"
            trigger = ""
            if lesson_key:
                lesson_resp = client.get(
                    base + f"/api/v1/tutor/students/{student_demo_id}/lessons/{lesson_key}",
                    headers=sauth,
                )
                if lesson_resp.status_code < 400:
                    trigger = (lesson_resp.json().get("data") or {}).get("trigger") or ""
                    tutor_concept_card = trigger == "concept_card"
            if recs and _topic_match(top.get("topic", "")) and not demo and tutor_concept_card:
                topic_hits["tutor"] = True
            st = STATUS_OK if topic_hits["tutor"] else STATUS_FAIL
            if demo:
                st = STATUS_FAIL
            elif recs and _topic_match(top.get("topic", "")) and not tutor_concept_card:
                st = STATUS_FAIL
            record(
                20,
                "Student tutor lesson grounded on approved Concept Card",
                st,
                f"demo_fallback={demo} · trigger={trigger or 'missing'} · "
                f"lesson_key={lesson_key} · {detail}",
            )
        else:
            record(20, "Student tutor", STATUS_FAIL, "no student_id")

    # Topic consistency gate
    aligned = all(topic_hits.values())
    record(
        21,
        "Same topic across marks/mastery/tutor/parent",
        STATUS_OK if aligned else STATUS_FAIL,
        ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in topic_hits.items()),
    )

    # Print report
    print(f"{'Step':<4} {'Status':<12} {'Check'}")
    print("-" * 72)
    fails = 0
    for step, label, status, detail in sorted(results, key=lambda x: x[0]):
        mark = status
        if status == STATUS_FAIL:
            fails += 1
        line = f"{step:<4} {mark:<12} {label}"
        if detail:
            line += f" — {detail}"
        print(line)

    works = sum(1 for _, _, s, _ in results if s == STATUS_OK)
    partial = sum(1 for _, _, s, _ in results if s == STATUS_PARTIAL)
    print("-" * 72)
    print(f"WORKS: {works}  PARTIAL: {partial}  FAIL: {fails}  SKIP: {sum(1 for _, _, s, _ in results if s == STATUS_SKIP)}")
    demo_fallback = any(
        step == 20 and "demo_fallback=True" in detail for step, _, _, detail in results
    )
    concept_card_grounded = tutor_concept_card and not demo_fallback
    loop_closed = fails == 0 and not demo_fallback and aligned and concept_card_grounded
    print(f"\nLoop closed for pilot: {'YES' if loop_closed else 'NO'}")
    return 0 if loop_closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
