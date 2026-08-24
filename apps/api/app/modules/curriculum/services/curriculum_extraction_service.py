"""Curriculum extraction — AI-assisted draft pack from syllabus/TOC inputs (Stage 2A).

Uses the shared LLM gateway and PackService; does not warehouse full textbooks.
File upload is deferred — paste structured curriculum text only.
"""
from __future__ import annotations

import re
import uuid
from typing import Optional

import structlog
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ai_usage import AIUsage
from app.db.models.file import FileCategory
from app.db.models.school import School
from app.modules.ai.gateway import LLMMessage, generate_llm, record_usage
from app.modules.ai.gateway.input_guard import sanitize_prompt_text
from app.modules.ai.gateway.json_parse import LLMJsonError, parse_llm_json
from app.modules.ai.services.ai_credits import credits_for_purpose, reserve_ai_credits
from app.modules.curriculum.schemas.onboarding import (
    CurriculumInputType,
    OnboardingProposeRequest,
    OnboardingProposeResponse,
)
from app.modules.curriculum.schemas.pack import ChapterIn, LearningOutcomeIn, PackCreate, TopicIn
from app.modules.curriculum.services.pack_audit import PackAuditEventType, record_pack_audit_event
from app.modules.curriculum.services.pack_service import PackService
from app.modules.files.services.document_ocr import extract_text_from_upload
from app.modules.files.services.file_service import FileService
from app.modules.files.services.file_validation import max_upload_bytes, read_file_bytes_bounded

logger = structlog.get_logger()

_PURPOSE = "curriculum_extraction"
_MAX_SOURCE_CHARS = 12000


class _ExtractedTopic(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    concepts: list[str] = []
    learning_outcomes: list[str] = []


class _ExtractedChapterModel(BaseModel):
    number: Optional[str] = Field(None, max_length=20)
    title: str = Field(..., min_length=1, max_length=200)
    topics: list[_ExtractedTopic] = []
    learning_outcomes: list[str] = []


class _ExtractionResult(BaseModel):
    chapters: list[_ExtractedChapterModel] = []
    low_confidence_notes: list[str] = []
    summary: Optional[str] = None


class CurriculumExtractionError(ValueError):
    """Extraction cannot proceed."""


def _line_based_chapters(text: str) -> list[_ExtractedChapterModel]:
    """Deterministic fallback when LLM output is empty (stub/dev)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    chapters: list[_ExtractedChapterModel] = []
    for i, line in enumerate(lines[:30]):
        m = re.match(r"^(?:chapter\s*)?(\d+)[\.\:\-\s]+(.+)$", line, re.I)
        if m:
            chapters.append(
                _ExtractedChapterModel(number=m.group(1), title=m.group(2).strip(), topics=[])
            )
        elif re.match(r"^\d+[\.\)]\s+", line):
            parts = re.split(r"[\.\)]\s+", line, maxsplit=1)
            num = parts[0].strip()
            title = parts[1].strip() if len(parts) > 1 else line
            chapters.append(_ExtractedChapterModel(number=num, title=title, topics=[]))
        else:
            chapters.append(
                _ExtractedChapterModel(number=str(i + 1), title=line[:200], topics=[])
            )
    return chapters


def _build_extraction_messages(
    *,
    board: str,
    book_title: str | None,
    input_type: CurriculumInputType,
    source_text: str,
) -> list[LLMMessage]:
    book_line = f"Textbook: {book_title}.\n" if book_title else ""
    system = (
        f"You are a curriculum structuring assistant for {board} schools in India. "
        "Extract a structured chapter → topic → concept hierarchy from the SOURCE TEXT. "
        "Do NOT invent chapters not supported by the source. "
        "Store only structured metadata — never reproduce long copyrighted passages. "
        "Return JSON only."
    )
    user = (
        f"Board: {board}.\n{book_line}"
        f"Input type: {input_type.value}.\n\n"
        f"SOURCE TEXT:\n{source_text}\n\n"
        "Return JSON:\n"
        '{"chapters": [{"number": str|null, "title": str, "topics": ['
        '{"title": str, "concepts": [str], "learning_outcomes": [str]}], '
        '"learning_outcomes": [str]}], '
        '"low_confidence_notes": [str], "summary": str|null}\n'
        "Include at least one topic per chapter when the source supports it."
    )
    return [LLMMessage("system", system), LLMMessage("user", user)]


class CurriculumExtractionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.packs = PackService(db)

    async def _resolve_source_text(
        self,
        *,
        request: OnboardingProposeRequest,
    ) -> tuple[str, str]:
        cleaned = sanitize_prompt_text(
            (request.curriculum_text or "").strip(),
            max_length=_MAX_SOURCE_CHARS,
            field_name="curriculum_text",
            reject_injection=False,
        )
        if not cleaned:
            raise CurriculumExtractionError(
                "No extractable curriculum text — paste a chapter list, syllabus, or TOC"
            )
        return cleaned[:_MAX_SOURCE_CHARS], "text"

    async def _resolve_curriculum_source(
        self,
        *,
        school_id: uuid.UUID,
        request: OnboardingProposeRequest,
    ) -> tuple[str, str]:
        raw_text = (request.curriculum_text or "").strip()
        source = "text"

        if not raw_text and request.file_id is not None:
            record = await FileService(self.db).get_file(request.file_id, school_id=school_id)
            if record is None:
                raise CurriculumExtractionError("Uploaded curriculum source not found")
            if record.category != FileCategory.DOCUMENT:
                raise CurriculumExtractionError(
                    "Only document uploads can be used as curriculum sources"
                )
            try:
                file_data = read_file_bytes_bounded(
                    record.storage_path,
                    size_bytes=record.size_bytes,
                    max_bytes=max_upload_bytes(FileCategory.DOCUMENT),
                )
            except ValueError as exc:
                raise CurriculumExtractionError(str(exc)) from exc
            raw_text = extract_text_from_upload(
                file_data=file_data,
                content_type=record.content_type,
            ).strip()
            source = "uploaded_document"

        cleaned = sanitize_prompt_text(
            raw_text,
            max_length=_MAX_SOURCE_CHARS,
            field_name="curriculum_source",
            reject_injection=False,
        )
        if not cleaned:
            raise CurriculumExtractionError(
                "No extractable curriculum source — upload a text-based PDF/image "
                "or paste a chapter list, syllabus, or TOC"
            )
        return cleaned[:_MAX_SOURCE_CHARS], source

    async def _call_llm(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        messages: list[LLMMessage],
        pack_id: uuid.UUID,
    ) -> tuple[_ExtractionResult, int]:
        cost = credits_for_purpose(_PURPOSE)
        reserved: AIUsage | None = None
        if cost > 0:
            reserved = await reserve_ai_credits(
                self.db,
                school_id,
                user_id=user_id,
                role=role,
                purpose_tag=_PURPOSE,
                feature="curriculum_extraction",
                credits=cost,
                ref_type="curriculum_pack",
            )
        result = await generate_llm(
            messages,
            json_mode=True,
            max_tokens=6000,
            temperature=0.2,
            feature="curriculum_extraction",
            caller="propose_draft_pack",
        )
        credits_used = 0
        if reserved:
            await record_usage(
                self.db,
                feature="curriculum_extraction",
                result=result,
                reserved_row=reserved,
                ref_type="curriculum_pack",
                ref_id=pack_id,
            )
            credits_used = reserved.credits_charged or cost
        try:
            raw = parse_llm_json(result.text, feature="curriculum_extraction")
            parsed = _ExtractionResult.model_validate(raw)
        except (LLMJsonError, ValidationError) as exc:
            logger.warning("curriculum_extraction_parse_failed", error=str(exc))
            parsed = _ExtractionResult(
                chapters=[],
                low_confidence_notes=["LLM output parse failed"],
            )
        return parsed, credits_used

    async def propose_draft_pack(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        request: OnboardingProposeRequest,
    ) -> OnboardingProposeResponse:
        source_text, extraction_source = await self._resolve_curriculum_source(
            school_id=school_id,
            request=request,
        )
        pack = await self.packs.create_pack(
            school_id,
            PackCreate(
                class_id=request.class_id,
                subject_id=request.subject_id,
                academic_year_id=request.academic_year_id,
                board=request.board,
                book_title=request.book_title,
                publisher=request.publisher,
                edition=request.edition,
            ),
            user_id,
        )
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=user_id,
            event_type=PackAuditEventType.EXTRACTION_STARTED,
            metadata={"input_type": request.input_type.value, "source": extraction_source},
        )
        school = await self.db.get(School, school_id)
        board = request.board or (school.board if school else "SSC")
        messages = _build_extraction_messages(
            board=board,
            book_title=request.book_title,
            input_type=request.input_type,
            source_text=source_text,
        )
        parsed, credits_used = await self._call_llm(
            school_id=school_id,
            user_id=user_id,
            role=role,
            messages=messages,
            pack_id=pack.id,
        )
        if not parsed.chapters:
            parsed.chapters = _line_based_chapters(source_text)
            parsed.low_confidence_notes = list(parsed.low_confidence_notes) + [
                "Used line-based fallback — add topics to each chapter before approval"
            ]
        chapters_in = []
        for idx, ch in enumerate(parsed.chapters):
            topics = [
                TopicIn(
                    title=t.title,
                    order_index=t_idx,
                    concepts=t.concepts[:12] or None,
                    learning_outcomes=[
                        LearningOutcomeIn(description=lo, order_index=lo_i)
                        for lo_i, lo in enumerate(t.learning_outcomes[:8])
                        if lo.strip()
                    ],
                )
                for t_idx, t in enumerate(ch.topics)
            ]
            chapters_in.append(
                ChapterIn(
                    number=ch.number or str(idx + 1),
                    title=ch.title,
                    order_index=idx,
                    topics=topics,
                    learning_outcomes=[
                        LearningOutcomeIn(description=lo, order_index=lo_i)
                        for lo_i, lo in enumerate(ch.learning_outcomes[:8])
                        if lo.strip()
                    ],
                )
            )
        await self.packs.populate_draft_structure(
            school_id,
            pack.id,
            chapters_in,
            actor_id=user_id,
        )
        await record_pack_audit_event(
            self.db,
            school_id=school_id,
            pack_id=pack.id,
            actor_id=user_id,
            event_type=PackAuditEventType.EXTRACTION_SUCCEEDED,
            metadata={
                "chapter_count": len(chapters_in),
                "topic_count": sum(len(c.topics) for c in chapters_in),
                "credits_used": credits_used,
            },
        )
        from app.modules.curriculum.services.pack_detail import build_pack_detail

        detail = await build_pack_detail(self.packs, pack)
        topic_count = sum(len(c.topics) for c in detail.chapters)
        return OnboardingProposeResponse(
            pack=detail,
            extraction_source=extraction_source,
            chapters_proposed=len(detail.chapters),
            topics_proposed=topic_count,
            low_confidence_notes=parsed.low_confidence_notes[:10],
            credits_used=credits_used,
        )
