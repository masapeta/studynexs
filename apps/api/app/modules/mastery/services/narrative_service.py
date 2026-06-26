"""Narrative drafting — the LLM verbalizes a flag's frozen evidence, nothing more.

Runs at approve time (zero cost for dismissed flags). The teacher sees and can
edit the exact text before anything is sent to a parent.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mastery import MasteryFlag
from app.modules.ai.gateway import LLMMessage, generate_llm, record_usage
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits

logger = structlog.get_logger()


def _build_messages(flag: MasteryFlag) -> list[LLMMessage]:
    ev = flag.evidence or {}
    history_lines = "\n".join(
        f"- {h.get('date')}: {h.get('title')} ({h.get('exam_type', '').replace('_', ' ')}): "
        f"{h.get('pct')}%"
        for h in ev.get("history", [])
    )
    trend = str(ev.get("trend", "stable")).replace("_", " ")
    system = (
        "You are an experienced Indian school teacher writing a short note to a "
        "parent about one topic their child needs support with. Write 3-5 warm, "
        "constructive sentences. Be specific about the topic, mention the recent "
        "scores pattern briefly without listing every number, and suggest one "
        "concrete way to practise this topic at home. Base everything STRICTLY on "
        "the data given — invent no facts, marks, or events. Never blame the child. "
        "Plain text only, no headings, bullets, or greetings like 'Dear parent'."
    )
    user = (
        f"Student: {ev.get('student_name') or 'the student'}\n"
        f"Subject: {ev.get('subject_name') or ''}\n"
        f"Topic needing support: {ev.get('topic')}\n"
        f"Current mastery: {ev.get('mastery_pct')}% (class average {ev.get('class_avg_pct')}%)\n"
        f"Trend: {trend}\n"
        f"Recent assessments:\n{history_lines or '- (none)'}\n\n"
        "Write the note to the parent."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


async def draft_narrative(
    db: AsyncSession,
    flag: MasteryFlag,
    *,
    created_by: uuid.UUID,
    role: str = "teacher",
    credits_charged: int | None = None,
) -> tuple[str, str]:
    """Draft the parent-facing note for an approved flag. Returns (text, model)."""
    cost = credits_charged if credits_charged is not None else credits_for_purpose("mastery_narrative")
    reserved = None
    if cost > 0:
        reserved = await reserve_ai_credits(
            db,
            flag.school_id,
            user_id=created_by,
            role=role,
            purpose_tag="mastery_narrative",
            feature="mastery_flag",
            credits=cost,
            ref_type="mastery_flag",
        )

    result = await generate_llm(
        _build_messages(flag), max_tokens=300, temperature=0.4,
        feature="mastery_flag", caller="draft_narrative",
    )
    model = result.model
    await record_usage(
        db,
        feature="mastery_flag",
        result=result,
        reserved_row=reserved,
        ref_type="mastery_flag",
        ref_id=flag.id,
    )
    text = (result.text or "").strip()
    if not text:
        raise ValueError("LLM returned an empty narrative")
    logger.info("mastery_narrative_drafted", flag_id=str(flag.id), model=model)
    return text, model
