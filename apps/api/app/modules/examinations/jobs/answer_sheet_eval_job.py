"""Arq handler — run answer sheet evaluation in the background."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jobs.worker import job_task
from app.modules.examinations.services.answer_sheet_eval_service import AnswerSheetEvalService


@job_task("answer_sheet_eval")
async def run_answer_sheet_eval(params: dict, db: AsyncSession) -> dict:
    evaluation_id = uuid.UUID(params["evaluation_id"])
    role = str(params.get("role") or "teacher")
    service = AnswerSheetEvalService(db)
    row = await service.execute_evaluation(evaluation_id, role=role)
    return {"evaluation_id": str(row.id), "status": row.status}
