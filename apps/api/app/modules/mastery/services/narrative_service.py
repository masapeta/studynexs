"""Narrative drafting — the LLM verbalizes a flag's frozen evidence, nothing more.

Runs at approve time (zero cost for dismissed flags). The teacher sees and can
edit the exact text before anything is sent to a parent.
"""
from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.mastery import MasteryFlag
from app.modules.ai.gateway import LLMMessage, default_model, get_provider, record_usage

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
) -> tuple[str, str]:
    """Draft the parent-facing note for an approved flag. Returns (text, model)."""
    provider = get_provider()
    model = default_model()
    result = await provider.generate(
        _build_messages(flag), model=model, max_tokens=300, temperature=0.4
    )
    await record_usage(
        db, feature="mastery_flag", result=result,
        school_id=flag.school_id, created_by=created_by,
    )
    text = (result.text or "").strip()
    if not text:
        raise ValueError("LLM returned an empty narrative")
    logger.info("mastery_narrative_drafted", flag_id=str(flag.id), model=model)
    return text, model
