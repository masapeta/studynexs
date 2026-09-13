from __future__ import annotations
import uuid
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.mastery import MasteryFlag
from app.modules.mastery.services.learning_evidence_service import LearningEvidenceService
from app.modules.ai.orchestration.tool_types import WorkspaceToolMetadata

class MarkEvidenceAsReviewedInput(BaseModel):
    flag_id: uuid.UUID = Field(..., description="ID of the mastery flag to review")

class MarkEvidenceAsReviewedOutput(BaseModel):
    status: str = Field(..., description="Success status")

async def mark_evidence_as_reviewed(
    db: AsyncSession,
    school_id: uuid.UUID,
    teacher_id: uuid.UUID,
    input: MarkEvidenceAsReviewedInput,
) -> MarkEvidenceAsReviewedOutput:
    service = LearningEvidenceService(db)
    await service.mark_as_reviewed(school_id, input.flag_id, teacher_id)
    return MarkEvidenceAsReviewedOutput(status="reviewed")

TOOL_HANDLER = mark_evidence_as_reviewed

TOOL_METADATA = WorkspaceToolMetadata(
    name="mark_evidence_as_reviewed",
    input_schema=MarkEvidenceAsReviewedInput,
    output_schema=MarkEvidenceAsReviewedOutput,
    read_only=False,
    side_effect_level="approval_required",
    requires_human_confirmation=True,
    idempotency_key_required=True,
    allowed_roles=["teacher", "class_incharge"],
    scope_rule="teacher_can_review_student_evidence",
    audit_event_type="workspace.write.mark_evidence_as_reviewed",
    pii_level="medium",
    max_payload_size=1024,
    tool_result_cache_policy="no_cache",
    timeout_ms=5000,
    retry_count=0,
    circuit_breaker_threshold=3,
    circuit_breaker_cooldown_seconds=300,
)
