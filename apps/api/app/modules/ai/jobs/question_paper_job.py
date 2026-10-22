"""Arq handler — generate a Question Paper in the background.

Mirrors the Answer-Sheet Evaluation job pattern: the request validates/authorizes and enqueues,
then this handler runs the EXISTING `generate_paper` pipeline on the worker. Generation is
unchanged (grounding, blueprint, validation, answer-key, credit reservation, provenance). The
QP domain lifecycle (`PaperStatus`) stays authoritative; the generic Job row carries only the
orchestration status + the resulting paper_id for the chat to poll.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs.worker import job_task


@job_task("question_paper_generate")
async def run_question_paper_generate(params: dict, db: AsyncSession) -> dict:
    from app.modules.ai.services.question_paper_service import generate_paper

    paper = await generate_paper(
        db,
        school_id=uuid.UUID(params["school_id"]),
        created_by=uuid.UUID(params["created_by"]),
        class_id=uuid.UUID(params["class_id"]),
        subject_id=uuid.UUID(params["subject_id"]),
        topics=[str(t) for t in (params.get("topics") or [])],
        total_marks=int(params["total_marks"]),
        duration_minutes=int(params.get("duration_minutes") or 180),
        difficulty=str(params.get("difficulty") or "balanced"),
        role=str(params.get("role") or "teacher"),
        purpose_tag=str(params.get("purpose_tag") or "qp_full"),
        credits_charged=params.get("credits_charged"),
        pack_id=uuid.UUID(params["pack_id"]) if params.get("pack_id") else None,
    )
    return {
        "paper_id": str(paper.id),
        "paper_status": paper.status.value if hasattr(paper.status, "value") else str(paper.status),
    }
