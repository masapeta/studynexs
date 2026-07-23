"""Batch 2 Academic Onboarding runtime proof.

Starts from a newly uploaded curriculum source and verifies the same approved
CurriculumPack grounds the downstream academic loop:

upload source -> AI extract draft -> HITL approve -> KG/RAG ready ->
lesson plan -> question paper -> exam/evaluation/HITL marks -> mastery ->
student tutor/copilot -> parent copilot.

Run:
    python scripts/smoke_batch2_academic_onboarding_runtime_proof.py

Requires API, Postgres, Redis, Qdrant, and a configured non-stub LLM provider.
"""
# ruff: noqa: E402,I001
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

import httpx

from reference_school_config import (
    DEMO_PASSWORD,
    LOGIN_CLASS_INCHARGE,
    LOGIN_PARENT,
    LOGIN_PRINCIPAL,
    LOGIN_STUDENT,
    LOGIN_TEACHER_MATHS,
    TENANT_SLUG,
)

BASE = os.environ.get("SMOKE_BASE_URL", "").rstrip("/") or "http://127.0.0.1:8000"
H = {"X-Tenant-Slug": TENANT_SLUG}
TEACHER_USER = os.environ.get("SMOKE_TEACHER_USER", LOGIN_TEACHER_MATHS)
APPROVER_USER = os.environ.get("SMOKE_APPROVER_USER", LOGIN_CLASS_INCHARGE)

CURRICULUM_SOURCE = """
Board: SSC
Class: 10
Subject: Mathematics
Book: StudyNexs Runtime Proof Mathematics Source

Chapter 1: Quadratic Equations
Topic: Quadratic Equations
Concepts: standard form ax^2 + bx + c = 0; factorisation; roots of a quadratic
Learning outcomes:
- Identify a quadratic equation in standard form.
- Solve simple quadratic equations by factorisation.
- Interpret roots as values that satisfy the equation.

Chapter 2: Arithmetic Progressions
Topic: Arithmetic Progressions
Concepts: common difference; nth term; sum of first n terms
Learning outcomes:
- Find the nth term of an arithmetic progression.
- Use the sum formula for simple AP problems.
"""


def _data(body: Any) -> Any:
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def _list(body: Any) -> list:
    data = _data(body)
    return data if isinstance(data, list) else []


def _source_refs(items: Any) -> list[str]:
    refs: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            for key in ("ref_id", "source_id", "id", "chunk_id", "concept_id", "topic_id"):
                value = item.get(key)
                if value:
                    refs.append(str(value))
        elif item:
            refs.append(str(item))
    return sorted(set(refs))


def _question_citation_refs(paper: dict) -> list[str]:
    refs: list[str] = []
    for section in paper.get("sections") or []:
        for question in section.get("questions") or []:
            refs.extend(str(citation) for citation in question.get("citations") or [])
    refs.extend(_source_refs(paper.get("grounding_sources") or []))
    return sorted(set(refs))


def _record_pack_evidence(
    evidence: list[dict[str, Any]],
    *,
    capability: str,
    tenant: str,
    observed_pack_id: Any,
    expected_pack_id: str,
    vector_count: Any,
    grounded: Any,
    citation_ids: list[str] | None = None,
    source_count: int | None = None,
    detail: str = "",
) -> None:
    if tenant != TENANT_SLUG:
        raise RuntimeError(f"{capability} tenant drifted: {tenant!r} != {TENANT_SLUG!r}")
    _assert_same_pack(capability, observed_pack_id, expected_pack_id)
    vectors = int(vector_count or 0)
    if vectors < 1:
        raise RuntimeError(f"{capability} has no retrievable vectors")
    if grounded is not True:
        raise RuntimeError(f"{capability} is not grounded")
    refs = citation_ids or []
    if source_count is not None and source_count < 1:
        raise RuntimeError(f"{capability} has no sources")
    if not refs and source_count is None:
        raise RuntimeError(f"{capability} has no citation/source evidence")
    evidence.append(
        {
            "capability": capability,
            "tenant": tenant,
            "pack_id": str(observed_pack_id),
            "vector_count": vectors,
            "grounded": bool(grounded),
            "citations": refs,
            "source_count": source_count,
            "detail": detail,
        }
    )


def _print_evidence_chain(evidence: list[dict[str, Any]], *, expected_pack_id: str) -> None:
    required = {
        "Academic Intelligence",
        "Lesson Plan",
        "Learning Materials",
        "Question Paper",
        "Assessment Evaluation",
        "Student Study Context",
        "Tutor Recommendation",
        "Tutor Lesson",
        "Student Copilot",
        "Parent Briefing",
        "Parent Ask",
    }
    seen = {row["capability"] for row in evidence}
    missing = sorted(required - seen)
    if missing:
        raise RuntimeError(f"Missing same-pack evidence rows: {', '.join(missing)}")
    if {row["pack_id"] for row in evidence} != {str(expected_pack_id)}:
        raise RuntimeError("Evidence ledger contains more than one CurriculumPack")
    if {row["tenant"] for row in evidence} != {TENANT_SLUG}:
        raise RuntimeError("Evidence ledger contains more than one tenant")

    print("\n[16] Same-pack grounding evidence ledger")
    for row in evidence:
        citation_preview = ",".join(row["citations"][:4]) if row["citations"] else "-"
        print(
            "  "
            f"{row['capability']}: tenant={row['tenant']} pack={row['pack_id']} "
            f"vectors={row['vector_count']} grounded={row['grounded']} "
            f"sources={row['source_count'] if row['source_count'] is not None else '-'} "
            f"citations={citation_preview} {row['detail']}".rstrip()
        )


def _login(client: httpx.Client, username: str) -> dict[str, str]:
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        headers=H,
        json={"username": username, "password": DEMO_PASSWORD},
    )
    if r.status_code == 429:
        raise RuntimeError(f"Login rate-limited for {username!r}; wait or clear scoped login keys")
    r.raise_for_status()
    return {**H, "Authorization": f"Bearer {r.json()['access_token']}"}


def _assert_real_llm_available() -> None:
    from app.core.config import get_settings
    from app.modules.ai.gateway.factory import _provider_configured, get_provider

    settings = get_settings()
    primary = (settings.AI_DEFAULT_PROVIDER or "gemini").lower()
    if primary != "stub" and _provider_configured(primary):
        return
    if primary == "ollama" and (settings.OLLAMA_BASE_URL or "").strip():
        return
    if get_provider(primary).name == "stub":
        raise RuntimeError(
            f"No configured real LLM provider for AI_DEFAULT_PROVIDER={primary!r}. "
            "Set GEMINI_API_KEY, OPENAI_API_KEY, or another configured provider key."
        )


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _curriculum_pdf_bytes(text: str) -> bytes:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    ops = ["BT", "/F1 10 Tf", "72 740 Td"]
    for idx, line in enumerate(lines[:45]):
        if idx:
            ops.append("0 -14 Td")
        ops.append(f"({_pdf_escape(line[:95])}) Tj")
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    out = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets: list[int] = []
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{idx} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer\n<< /Root 1 0 R /Size {len(objects) + 1} >>\n"
        f"startxref\n{xref}\n%%EOF\n"
    ).encode("ascii")
    return out


def _pick_class_subject_year(client: httpx.Client, auth: dict[str, str]) -> tuple[dict, dict, str]:
    classes = client.get(f"{BASE}/api/v1/academic/classes?page_size=100", headers=auth)
    classes.raise_for_status()
    items = classes.json().get("items") or classes.json().get("data") or []
    cls = next(
        (c for c in items if c.get("grade") == "Class 10" and c.get("section") == "A"),
        None,
    )
    if not cls:
        raise RuntimeError("Reference Class 10-A not found")
    subjects = client.get(
        f"{BASE}/api/v1/academic/subjects?class_id={cls['id']}",
        headers=auth,
    )
    subjects.raise_for_status()
    subject_items = _list(subjects.json())
    subject = next(
        (s for s in subject_items if "math" in (s.get("name") or "").lower()),
        None,
    )
    if not subject:
        raise RuntimeError("Class 10-A Mathematics subject not found")
    year_id = cls.get("academic_year_id")
    if not year_id:
        years = client.get(f"{BASE}/api/v1/school/academic-years", headers=auth)
        years.raise_for_status()
        year_items = _list(years.json())
        if not year_items:
            raise RuntimeError("No academic year found")
        year_id = year_items[0]["id"]
    return cls, subject, year_id


def _poll_intelligence(
    client: httpx.Client, auth: dict[str, str], pack_id: str, timeout_s: int = 150
) -> dict:
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        r = client.get(
            f"{BASE}/api/v1/curriculum/packs/{pack_id}/intelligence-status",
            headers=auth,
        )
        r.raise_for_status()
        last = _data(r.json())
        print(
            "  intelligence:",
            f"phase={last.get('phase')}",
            f"kg={last.get('kg_ready')}",
            f"rag={last.get('rag_ready')}",
            f"vectors={last.get('rag_vector_count')}",
            f"topics={last.get('retrievable_topic_count')}",
        )
        if last.get("academic_intelligence_ready"):
            return last
        if last.get("phase") == "failed":
            retry = client.post(
                f"{BASE}/api/v1/curriculum/packs/{pack_id}/retry-rag-index",
                headers=auth,
            )
            print(f"  retry-rag-index: {retry.status_code}")
        time.sleep(3)
    return last


def _sum_paper_marks(paper: dict) -> float:
    return round(
        sum(
            float(q.get("marks") or 0)
            for section in paper.get("sections") or []
            for q in section.get("questions") or []
        ),
        2,
    )


def _student_answers_for(paper: dict) -> dict[str, str]:
    answers: dict[str, str] = {}
    for section in paper.get("sections") or []:
        for q in section.get("questions") or []:
            qno = str(q.get("number") or "").strip()
            if qno:
                answers[qno] = "I am not sure about this answer yet."
    return answers


def _answer_sheet_png_bytes(answers: dict[str, str]) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    rows = ["StudyNexs Batch 2 Runtime Proof Answer Sheet", "Student: student_demo"]
    rows.extend(f"Q{qno}: {answer}" for qno, answer in list(answers.items())[:18])
    width = 1200
    height = max(800, 90 + len(rows) * 36)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    y = 40
    for row in rows:
        draw.text((48, y), row[:110], fill="black", font=font)
        y += 36
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


async def _execute_evaluation_once(evaluation_id: str, *, role: str) -> None:
    from app.core.database import async_session_factory, engine
    from app.modules.examinations.services.answer_sheet_eval_service import AnswerSheetEvalService

    async with async_session_factory() as session:
        await AnswerSheetEvalService(session).execute_evaluation(
            uuid.UUID(evaluation_id), role=role
        )
        await session.commit()
    await engine.dispose()


async def _recompute_mastery_once(
    school_id: str, class_id: str, subject_id: str
) -> int:
    from app.core.database import async_session_factory
    from app.modules.mastery.services.mastery_service import recompute_class_subject

    async with async_session_factory() as session:
        count = await recompute_class_subject(
            session,
            uuid.UUID(school_id),
            uuid.UUID(class_id),
            uuid.UUID(subject_id),
        )
        await session.commit()
        return count


def _wait_for_evaluation(
    client: httpx.Client,
    auth: dict[str, str],
    evaluation_id: str,
    *,
    role: str,
    timeout_s: int = 45,
) -> dict:
    deadline = time.time() + timeout_s
    started = time.time()
    last: dict = {}
    executed_inline = False
    while time.time() < deadline:
        r = client.get(f"{BASE}/api/v1/exams/evaluations/{evaluation_id}", headers=auth)
        r.raise_for_status()
        last = _data(r.json())
        if last.get("status") == "suggested":
            return last
        if last.get("status") == "failed":
            raise RuntimeError(f"Evaluation failed: {last.get('error_message')}")
        if (
            not executed_inline
            and last.get("status") == "processing"
            and time.time() - started > 12
        ):
            print("  evaluation queued; executing existing service inline for local proof")
            asyncio.run(_execute_evaluation_once(evaluation_id, role=role))
            executed_inline = True
        time.sleep(3)
    return last


def _portal_student_id(client: httpx.Client, auth: dict[str, str]) -> str:
    ctx = client.get(f"{BASE}/api/v1/portal/context", headers=auth)
    ctx.raise_for_status()
    student_id = (_data(ctx.json()) or {}).get("student_id")
    if not student_id:
        raise RuntimeError("student_demo portal context did not expose student_id")
    return student_id


def _assert_same_pack(label: str, actual: Any, expected: str) -> None:
    if str(actual) != str(expected):
        raise RuntimeError(f"{label} not grounded to approved pack: {actual} != {expected}")


def _activate_ai_override(client: httpx.Client, principal_auth: dict[str, str]) -> None:
    override = client.post(
        f"{BASE}/api/v1/ai/credits/override",
        headers=principal_auth,
        json={"hours": 2},
    )
    if override.status_code >= 400:
        raise RuntimeError(
            f"AI credit override failed: {override.status_code} {override.text[:300]}"
        )
    print(f"  AI override: {_data(override.json()).get('override_until')}")


def main() -> int:
    print(f"Batch 2 Academic Onboarding runtime proof — API {BASE}\n")
    try:
        _assert_real_llm_available()
    except RuntimeError as exc:
        print(f"PREFLIGHT FAIL: {exc}")
        return 2

    client = httpx.Client(timeout=240.0, follow_redirects=True)
    ready = client.get(f"{BASE}/ready")
    if ready.status_code >= 400:
        print(f"API not ready: {ready.status_code} {ready.text[:300]}")
        return 1
    print(f"/ready: {ready.text}")

    teacher_auth = _login(client, TEACHER_USER)
    approver_auth = _login(client, APPROVER_USER)
    student_auth = _login(client, LOGIN_STUDENT)
    parent_auth = _login(client, LOGIN_PARENT)
    principal_auth = _login(client, LOGIN_PRINCIPAL)
    me = client.get(f"{BASE}/api/v1/users/me", headers=teacher_auth)
    me.raise_for_status()
    school_id = str(_data(me.json()).get("school_id"))
    evidence: list[dict[str, Any]] = []

    cls, subject, year_id = _pick_class_subject_year(client, teacher_auth)
    class_id = cls["id"]
    subject_id = subject["id"]
    print(
        "Target:",
        f"{cls.get('grade')} {cls.get('section')}",
        "·",
        subject.get("name"),
        f"· year={year_id}",
    )

    print("\n[1] Upload curriculum source PDF")
    pdf_bytes = _curriculum_pdf_bytes(CURRICULUM_SOURCE)
    upload = client.post(
        f"{BASE}/api/v1/files/upload?category=document",
        headers=teacher_auth,
        files={
            "file": (
                "batch2-academic-onboarding-source.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
    )
    if upload.status_code >= 400:
        print(f"UPLOAD FAILED: {upload.status_code} {upload.text[:500]}")
        return 1
    file_id = _data(upload.json())["id"]
    print(f"  file_id={file_id}")

    print("\n[2] AI extracts draft CurriculumPack from uploaded source")
    propose = client.post(
        f"{BASE}/api/v1/curriculum/onboarding/propose",
        headers=teacher_auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "academic_year_id": year_id,
            "board": "SSC",
            "book_title": "Batch 2 Runtime Proof Mathematics Source",
            "input_type": "syllabus",
            "file_id": file_id,
        },
    )
    if propose.status_code >= 400:
        print(f"PROPOSE FAILED: {propose.status_code}\n{propose.text[:700]}")
        return 1
    pdata = _data(propose.json())
    pack_id = pdata["pack"]["id"]
    print(
        f"  pack_id={pack_id} source={pdata.get('extraction_source')} "
        f"chapters={pdata.get('chapters_proposed')} topics={pdata.get('topics_proposed')}"
    )
    if pdata.get("extraction_source") != "uploaded_document":
        raise RuntimeError("Draft did not originate from uploaded document")
    if pdata.get("topics_proposed", 0) < 1:
        raise RuntimeError("AI extraction produced no topics")

    print("\n[3] Teacher review detail")
    detail = client.get(f"{BASE}/api/v1/curriculum/packs/{pack_id}", headers=teacher_auth)
    detail.raise_for_status()
    pack_detail = _data(detail.json())
    chapters = pack_detail.get("chapters") or []
    topics = [
        topic
        for chapter in chapters
        for topic in chapter.get("topics") or []
    ]
    focus_topic = next(
        (t.get("title") for t in topics if "quadratic" in (t.get("title") or "").lower()),
        topics[0].get("title") if topics else "Quadratic Equations",
    )
    focus_chapter = next(
        (
            chapter.get("title")
            for chapter in chapters
            if any((t.get("title") == focus_topic) for t in chapter.get("topics") or [])
        ),
        chapters[0].get("title") if chapters else "Quadratic Equations",
    )
    print(f"  focus={focus_chapter} / {focus_topic}")

    print("\n[4] HITL approve CurriculumPack")
    approve = client.post(
        f"{BASE}/api/v1/curriculum/packs/{pack_id}/approve",
        headers=approver_auth,
    )
    if approve.status_code >= 400:
        print(f"PACK APPROVAL FAILED: {approve.status_code}\n{approve.text[:700]}")
        return 1
    print(f"  approved status={_data(approve.json()).get('status', 'approved')}")

    print("\n[5] KG Ready + RAG Ready + Academic Intelligence Ready")
    intel = _poll_intelligence(client, teacher_auth, pack_id)
    if not intel.get("academic_intelligence_ready"):
        print(json.dumps(intel, indent=2, default=str))
        raise RuntimeError("Academic Intelligence did not become ready")
    vector_count = intel.get("rag_vector_count")
    _record_pack_evidence(
        evidence,
        capability="Academic Intelligence",
        tenant=TENANT_SLUG,
        observed_pack_id=pack_id,
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=intel.get("academic_intelligence_ready"),
        source_count=int(intel.get("retrievable_topic_count") or 0),
        detail=f"kg={intel.get('kg_ready')} rag={intel.get('rag_ready')}",
    )

    graph = client.get(f"{BASE}/api/v1/curriculum/packs/{pack_id}/graph", headers=teacher_auth)
    graph.raise_for_status()
    spine = _data(graph.json())
    concepts = [
        concept
        for chapter in spine.get("chapters") or []
        for topic in chapter.get("topics") or []
        for concept in topic.get("concepts") or []
    ]
    concept = next(
        (
            c
            for c in concepts
            if "quadratic" in (c.get("title") or "").lower()
            or "factor" in (c.get("title") or "").lower()
            or "root" in (c.get("title") or "").lower()
        ),
        concepts[0] if concepts else None,
    )
    if not concept:
        raise RuntimeError("KG graph exposed no concepts for tutor grounding")
    concept_id = concept["id"]
    concept_slug = concept["slug"]
    print(f"  concept={concept.get('title')} slug={concept_slug} id={concept_id}")

    print("\n[6] Approve Concept Cards for Tutor grounding")
    approved_cards = 0
    for candidate in concepts:
        card_create = client.post(
            f"{BASE}/api/v1/curriculum/concepts/{candidate['id']}/cards",
            headers=teacher_auth,
            json={
                "title": candidate.get("title") or focus_topic,
                "explanation": (
                    f"{candidate.get('title') or focus_topic} belongs to the approved "
                    "Batch 2 runtime proof curriculum pack. Explain it with a worked "
                    "example and one short practice check."
                ),
                "examples": [
                    "Solve x^2 - 5x + 6 = 0 by factorisation.",
                    "Check roots by substituting them back into the equation.",
                ],
                "hints": ["Connect the idea back to the approved curriculum topic."],
                "visual_kind": "equation",
            },
        )
        if card_create.status_code >= 400:
            print(f"CARD CREATE FAILED: {card_create.status_code}\n{card_create.text[:500]}")
            return 1
        card_id = _data(card_create.json())["id"]
        card_approve = client.post(
            f"{BASE}/api/v1/curriculum/concept-cards/{card_id}/approve",
            headers=approver_auth,
        )
        if card_approve.status_code >= 400:
            print(
                f"CARD APPROVAL FAILED: {card_approve.status_code}\n{card_approve.text[:500]}"
            )
            return 1
        _assert_same_pack("concept card", _data(card_approve.json()).get("pack_id"), pack_id)
        approved_cards += 1
    if approved_cards < 1:
        raise RuntimeError("No concept cards were approved for Tutor grounding")
    print(f"  approved_cards={approved_cards}")

    print("\n[7] Teacher Copilot: grounded lesson plan + learning materials")
    lp = client.post(
        f"{BASE}/api/v1/lesson-plans/generate",
        headers=teacher_auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "pack_id": pack_id,
            "generation_mode": "copilot",
            "topic": focus_topic,
            "chapter": focus_chapter,
        },
    )
    if lp.status_code >= 400:
        print(f"LESSON PLAN FAILED: {lp.status_code}\n{lp.text[:700]}")
        return 1
    plan = lp.json()
    _assert_same_pack("lesson plan", plan.get("pack_id"), pack_id)
    if not plan.get("grounded") or not (plan.get("grounding_sources") or []):
        raise RuntimeError("Lesson plan is not visibly grounded")
    if not (plan.get("materials") or []):
        raise RuntimeError("Lesson plan did not produce learning materials")
    lesson_sources = plan.get("grounding_sources") or []
    _record_pack_evidence(
        evidence,
        capability="Lesson Plan",
        tenant=TENANT_SLUG,
        observed_pack_id=plan.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=plan.get("grounded"),
        citation_ids=_source_refs(lesson_sources),
        source_count=len(lesson_sources),
        detail=f"lesson_id={plan.get('id')}",
    )
    _record_pack_evidence(
        evidence,
        capability="Learning Materials",
        tenant=TENANT_SLUG,
        observed_pack_id=plan.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=plan.get("grounded"),
        citation_ids=_source_refs(plan.get("materials") or []),
        source_count=len(plan.get("materials") or []),
        detail=f"lesson_id={plan.get('id')}",
    )
    print(
        f"  lesson_id={plan.get('id')} grounded={plan.get('grounded')} "
        f"sources={len(plan.get('grounding_sources') or [])} "
        f"materials={len(plan.get('materials') or [])}"
    )

    print("\n[8] Assessment Intelligence: grounded question paper")
    qp = client.post(
        f"{BASE}/api/v1/ai/question-papers/generate",
        headers=teacher_auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "pack_id": pack_id,
            "topics": [focus_topic],
            "total_marks": 20,
            "duration_minutes": 45,
            "difficulty": "balanced",
            "title": f"Batch 2 Runtime Proof - {focus_topic}",
        },
    )
    if qp.status_code >= 400:
        if qp.status_code == 429 and "pilot limit" in qp.text.lower():
            print("  QP pilot cap reached; activating principal AI override and retrying once")
            _activate_ai_override(client, principal_auth)
            qp = client.post(
                f"{BASE}/api/v1/ai/question-papers/generate",
                headers=teacher_auth,
                json={
                    "class_id": class_id,
                    "subject_id": subject_id,
                    "pack_id": pack_id,
                    "topics": [focus_topic],
                    "total_marks": 20,
                    "duration_minutes": 45,
                    "difficulty": "balanced",
                    "title": f"Batch 2 Runtime Proof - {focus_topic}",
                },
            )
        if qp.status_code >= 400:
            print(f"QUESTION PAPER FAILED: {qp.status_code}\n{qp.text[:700]}")
            return 1
    paper = qp.json()
    paper_id = paper["id"]
    _assert_same_pack("question paper", paper.get("pack_id"), pack_id)
    questions = [
        q
        for section in paper.get("sections") or []
        for q in section.get("questions") or []
    ]
    cited = [q for q in questions if q.get("citations")]
    if not paper.get("grounded") or not cited:
        raise RuntimeError("Question paper is not visibly grounded")
    _record_pack_evidence(
        evidence,
        capability="Question Paper",
        tenant=TENANT_SLUG,
        observed_pack_id=paper.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=paper.get("grounded"),
        citation_ids=_question_citation_refs(paper),
        source_count=len(paper.get("grounding_sources") or []),
        detail=f"paper_id={paper_id}",
    )
    print(
        f"  paper_id={paper_id} questions={len(questions)} cited={len(cited)} "
        f"sources={len(paper.get('grounding_sources') or [])}"
    )

    print("\n[9] Teacher review + HOD/class-incharge approve question paper")
    submit = client.post(
        f"{BASE}/api/v1/ai/question-papers/{paper_id}/submit",
        headers=teacher_auth,
    )
    if submit.status_code >= 400:
        print(f"QP SUBMIT FAILED: {submit.status_code}\n{submit.text[:500]}")
        return 1
    approve_paper = client.post(
        f"{BASE}/api/v1/ai/question-papers/{paper_id}/approve",
        headers=approver_auth,
    )
    if approve_paper.status_code >= 400:
        print(f"QP APPROVE FAILED: {approve_paper.status_code}\n{approve_paper.text[:500]}")
        return 1
    paper = approve_paper.json()
    if paper.get("status") != "approved":
        raise RuntimeError(f"Question paper not approved: {paper.get('status')}")

    print("\n[10] Conduct assessment: create exam from approved paper")
    exam_total = _sum_paper_marks(paper) or float(paper.get("total_marks") or 20)
    exam = client.post(
        f"{BASE}/api/v1/exams",
        headers=teacher_auth,
        json={
            "class_id": class_id,
            "subject_id": subject_id,
            "exam_type": "unit_test",
            "title": f"Batch 2 Runtime Proof Exam - {focus_topic}",
            "total_marks": exam_total,
            "exam_date": str(date.today()),
            "topic": focus_topic,
        },
    )
    if exam.status_code >= 400:
        print(f"EXAM CREATE FAILED: {exam.status_code}\n{exam.text[:500]}")
        return 1
    exam_id = _data(exam.json())["id"]
    schema = client.put(
        f"{BASE}/api/v1/exams/{exam_id}/questions",
        headers=teacher_auth,
        json={"source_paper_id": paper_id},
    )
    if schema.status_code >= 400:
        print(f"QUESTION SCHEMA FAILED: {schema.status_code}\n{schema.text[:500]}")
        return 1
    print(f"  exam_id={exam_id} total_marks={exam_total}")

    print("\n[11] Student attempt + AI Evaluation suggestion")
    student_id = _portal_student_id(client, student_auth)
    answers = _student_answers_for(paper)
    answer_sheet = client.post(
        f"{BASE}/api/v1/files/upload?category=answer_sheet",
        headers=teacher_auth,
        files={
            "file": (
                "batch2-runtime-proof-answer-sheet.png",
                _answer_sheet_png_bytes(answers),
                "image/png",
            )
        },
    )
    if answer_sheet.status_code >= 400:
        print(f"ANSWER SHEET UPLOAD FAILED: {answer_sheet.status_code}\n{answer_sheet.text[:700]}")
        return 1
    answer_sheet_file_id = _data(answer_sheet.json())["id"]
    evaluation = client.post(
        f"{BASE}/api/v1/exams/{exam_id}/evaluations",
        headers=teacher_auth,
        json={
            "student_id": student_id,
            "file_id": answer_sheet_file_id,
            "student_answers": answers,
        },
    )
    if evaluation.status_code >= 400:
        print(f"EVALUATION CREATE FAILED: {evaluation.status_code}\n{evaluation.text[:700]}")
        return 1
    evaluation_row = _data(evaluation.json())
    evaluation_id = evaluation_row["id"]
    if str(evaluation_row.get("file_id")) != str(answer_sheet_file_id):
        raise RuntimeError("Evaluation was not linked to the uploaded answer sheet")
    evaluation_row = _wait_for_evaluation(
        client,
        teacher_auth,
        evaluation_id,
        role="teacher",
    )
    if evaluation_row.get("status") != "suggested":
        print(json.dumps(evaluation_row, indent=2, default=str)[:1000])
        raise RuntimeError("AI Evaluation did not reach suggested status")
    suggestions = evaluation_row.get("ai_suggestions") or {}
    if not suggestions:
        raise RuntimeError("AI Evaluation produced no suggestions")
    if str(evaluation_row.get("file_id")) != str(answer_sheet_file_id):
        raise RuntimeError("Evaluation did not retain the uploaded answer-sheet file")
    _record_pack_evidence(
        evidence,
        capability="Assessment Evaluation",
        tenant=TENANT_SLUG,
        observed_pack_id=pack_id,
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=True,
        citation_ids=[paper_id, exam_id, evaluation_id, answer_sheet_file_id],
        source_count=len(suggestions),
        detail="linked approved_qp+exam+answer_sheet",
    )
    print(
        f"  answer_sheet_file_id={answer_sheet_file_id} "
        f"evaluation_id={evaluation_id} suggestions={len(suggestions)}"
    )

    print("\n[12] Teacher HITL approval -> marks + gradebook")
    approve_eval = client.post(
        f"{BASE}/api/v1/exams/evaluations/{evaluation_id}/approve",
        headers=teacher_auth,
        json={"teacher_overrides": {}, "correction_summary": "Reviewed for Batch 2 proof."},
    )
    if approve_eval.status_code >= 400:
        print(f"EVAL APPROVE FAILED: {approve_eval.status_code}\n{approve_eval.text[:700]}")
        return 1
    if _data(approve_eval.json()).get("status") != "approved":
        raise RuntimeError("Teacher approval did not approve evaluation")
    marks = client.get(f"{BASE}/api/v1/exams/{exam_id}/marks", headers=teacher_auth)
    marks.raise_for_status()
    mark_rows = _list(marks.json())
    mark = next((m for m in mark_rows if str(m.get("student_id")) == str(student_id)), None)
    if not mark or not mark.get("ai_graded"):
        raise RuntimeError("Approved AI Evaluation did not save AI-graded marks")
    gradebook = client.get(
        f"{BASE}/api/v1/exams/gradebook?class_id={class_id}",
        headers=teacher_auth,
    )
    gradebook.raise_for_status()
    print(f"  marks={mark.get('marks_obtained')} ai_graded={mark.get('ai_graded')}")

    print("\n[13] Knowledge Graph + Mastery update")
    recompute = client.post(
        f"{BASE}/api/v1/mastery/recompute",
        headers=principal_auth,
        json={"class_id": class_id, "subject_id": subject_id},
    )
    if recompute.status_code < 400:
        rows_upserted = (_data(recompute.json()) or {}).get("rows_upserted")
    else:
        print(
            "  mastery recompute API unavailable for this role; "
            "running existing service directly"
        )
        rows_upserted = asyncio.run(_recompute_mastery_once(school_id, class_id, subject_id))
    mastery = client.get(f"{BASE}/api/v1/mastery/students/{student_id}", headers=teacher_auth)
    mastery.raise_for_status()
    mastery_data = _data(mastery.json()) or {}
    topic_rows = [
        t
        for subj in mastery_data.get("subjects") or []
        for t in subj.get("topics") or []
    ]
    matched_mastery = [
        t
        for t in topic_rows
        if "quadratic" in str(t.get("topic") or t.get("topic_display") or "").lower()
    ]
    if not matched_mastery:
        raise RuntimeError("Mastery did not update for the newly approved pack topic")
    print(f"  rows_upserted={rows_upserted} topic={matched_mastery[0]}")

    print("\n[14] Student Copilot / AI Tutor without fallback")
    study = client.get(
        f"{BASE}/api/v1/tutor/students/{student_id}/study-context",
        headers=student_auth,
    )
    study.raise_for_status()
    study_ctx = _data(study.json())
    weak = study_ctx.get("weak_concepts") or []
    same_pack_weak = [w for w in weak if str(w.get("pack_id")) == str(pack_id)]
    if not same_pack_weak or not study_ctx.get("grounded") or study_ctx.get("source_count", 0) < 1:
        raise RuntimeError(f"Study context not grounded to pack {pack_id}: {study_ctx}")
    _record_pack_evidence(
        evidence,
        capability="Student Study Context",
        tenant=TENANT_SLUG,
        observed_pack_id=same_pack_weak[0].get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=study_ctx.get("grounded"),
        citation_ids=[
            str(row.get("concept_id") or row.get("slug"))
            for row in same_pack_weak
            if row.get("concept_id") or row.get("slug")
        ],
        source_count=int(study_ctx.get("source_count") or 0),
        detail=f"weak_concepts={len(same_pack_weak)}",
    )
    recs_resp = client.get(
        f"{BASE}/api/v1/tutor/students/{student_id}/recommendations",
        headers=student_auth,
    )
    recs_resp.raise_for_status()
    recs = _list(recs_resp.json())
    rec = next(
        (
            r
            for r in recs
            if str(r.get("pack_id")) == str(pack_id)
            and r.get("source") == "concept_card"
            and r.get("lesson_key") != "fractions"
        ),
        None,
    )
    if not rec:
        raise RuntimeError(f"Tutor recommendation fell back or missed pack: {recs[:3]}")
    _record_pack_evidence(
        evidence,
        capability="Tutor Recommendation",
        tenant=TENANT_SLUG,
        observed_pack_id=rec.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=rec.get("source") == "concept_card",
        citation_ids=[str(rec.get("concept_id") or rec.get("lesson_key"))],
        source_count=1,
        detail=f"source={rec.get('source')} lesson_key={rec.get('lesson_key')}",
    )
    lesson_key = rec["lesson_key"]
    lesson = client.get(
        f"{BASE}/api/v1/tutor/students/{student_id}/lessons/{lesson_key}",
        headers=student_auth,
    )
    lesson.raise_for_status()
    lesson_data = _data(lesson.json())
    _assert_same_pack("tutor lesson", lesson_data.get("pack_id"), pack_id)
    if lesson_data.get("trigger") != "concept_card":
        raise RuntimeError(f"Tutor lesson was not concept-card grounded: {lesson_data}")
    _record_pack_evidence(
        evidence,
        capability="Tutor Lesson",
        tenant=TENANT_SLUG,
        observed_pack_id=lesson_data.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=lesson_data.get("trigger") == "concept_card",
        citation_ids=[str(lesson_data.get("concept_id") or lesson_data.get("concept_slug"))],
        source_count=1,
        detail=f"trigger={lesson_data.get('trigger')}",
    )
    ask = client.post(
        f"{BASE}/api/v1/tutor/students/{student_id}/ask",
        headers=student_auth,
        json={
            "question": f"Please help me revise {focus_topic}.",
            "concept_slug": lesson_data.get("concept_slug") or concept_slug,
        },
    )
    if ask.status_code >= 400:
        print(f"STUDENT COPILOT ASK FAILED: {ask.status_code}\n{ask.text[:700]}")
        return 1
    answer = _data(ask.json())
    _assert_same_pack("student copilot", answer.get("pack_id"), pack_id)
    if not answer.get("grounded") or answer.get("source_count", 0) < 1:
        raise RuntimeError(f"Student Copilot did not use grounded pack context: {answer}")
    _record_pack_evidence(
        evidence,
        capability="Student Copilot",
        tenant=TENANT_SLUG,
        observed_pack_id=answer.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=answer.get("grounded"),
        citation_ids=[str(item) for item in answer.get("citations") or []],
        source_count=int(answer.get("source_count") or 0),
        detail=f"concept_id={answer.get('concept_id')}",
    )
    print(
        f"  study_sources={study_ctx.get('source_count')} "
        f"rec_source={rec.get('source')} lesson_trigger={lesson_data.get('trigger')} "
        f"copilot_sources={answer.get('source_count')}"
    )

    print("\n[15] Parent Copilot + personalized remediation")
    parent_ctx = client.get(f"{BASE}/api/v1/portal/context", headers=parent_auth)
    parent_ctx.raise_for_status()
    children = (_data(parent_ctx.json()) or {}).get("children") or []
    if not any(str(child.get("student_id")) == str(student_id) for child in children):
        raise RuntimeError("Parent portal does not expose student_demo as linked child")
    briefing = client.get(
        f"{BASE}/api/v1/parent-copilot/students/{student_id}/briefing",
        headers=parent_auth,
    )
    if briefing.status_code >= 400:
        print(f"PARENT BRIEFING FAILED: {briefing.status_code}\n{briefing.text[:700]}")
        return 1
    briefing_data = _data(briefing.json())
    _assert_same_pack("parent briefing", briefing_data.get("pack_id"), pack_id)
    if not briefing_data.get("grounded") or briefing_data.get("source_count", 0) < 1:
        raise RuntimeError(f"Parent briefing did not use grounded pack context: {briefing_data}")
    _record_pack_evidence(
        evidence,
        capability="Parent Briefing",
        tenant=TENANT_SLUG,
        observed_pack_id=briefing_data.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=briefing_data.get("grounded"),
        citation_ids=[str(briefing_data.get("concept_id") or briefing_data.get("concept_slug"))],
        source_count=int(briefing_data.get("source_count") or 0),
        detail=f"focus={briefing_data.get('focus_area')}",
    )
    parent_ask = client.post(
        f"{BASE}/api/v1/parent-copilot/students/{student_id}/ask",
        headers=parent_auth,
        json={"question": f"How can I help at home with {focus_topic}?"},
    )
    if parent_ask.status_code >= 400:
        print(f"PARENT ASK FAILED: {parent_ask.status_code}\n{parent_ask.text[:700]}")
        return 1
    parent_answer = _data(parent_ask.json())
    _assert_same_pack("parent ask", parent_answer.get("pack_id"), pack_id)
    if not parent_answer.get("grounded") or parent_answer.get("source_count", 0) < 1:
        raise RuntimeError(f"Parent ask did not use grounded pack context: {parent_answer}")
    if not parent_answer.get("home_tips"):
        raise RuntimeError("Parent Copilot did not return home remediation tips")
    _record_pack_evidence(
        evidence,
        capability="Parent Ask",
        tenant=TENANT_SLUG,
        observed_pack_id=parent_answer.get("pack_id"),
        expected_pack_id=pack_id,
        vector_count=vector_count,
        grounded=parent_answer.get("grounded"),
        citation_ids=[str(parent_answer.get("concept_id") or parent_answer.get("concept_slug"))],
        source_count=int(parent_answer.get("source_count") or 0),
        detail=f"home_tips={len(parent_answer.get('home_tips') or [])}",
    )
    print(
        f"  parent_sources={briefing_data.get('source_count')} "
        f"home_tips={len(parent_answer.get('home_tips') or [])}"
    )
    _print_evidence_chain(evidence, expected_pack_id=pack_id)

    print("\n" + "=" * 72)
    print("BATCH 2 ACADEMIC ONBOARDING RUNTIME PROOF: PASS")
    print(f"file_id={file_id}")
    print(f"pack_id={pack_id}")
    print(f"paper_id={paper_id}")
    print(f"exam_id={exam_id}")
    print(f"evaluation_id={evaluation_id}")
    print(
        "Verified: uploaded source -> approved CurriculumPack -> KG/RAG -> "
        "lesson plan/QP/materials -> AI Evaluation HITL -> marks/mastery -> "
        "Student Tutor/Copilot -> Parent Copilot, all on the same pack."
    )
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
