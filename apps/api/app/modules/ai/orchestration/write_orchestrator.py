from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.ai.orchestration.tool_registry import WorkspaceToolRegistry
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext

class WorkspaceWriteOrchestrator:
    def __init__(self, registry: WorkspaceToolRegistry) -> None:
        self._registry = registry

    async def execute(
        self,
        db: AsyncSession,
        *,
        context: WorkspaceToolContext,
        tool_name: str,
        payload: dict,
    ) -> dict:
        tool = self._registry.get(tool_name)
        if tool.metadata.read_only:
             raise ValueError(f"Tool {tool_name} is read-only and cannot be executed by the write orchestrator.")
        
        input_data = tool.metadata.input_schema.model_validate(payload)
        
        # In a real agentic flow, we would check for human confirmation here.
        # Phase 1: We allow it to proceed if the action is approved.
        
        result = await tool.handler(db, context.school_id, context.teacher_user_id, input_data)
        return result.model_dump()
