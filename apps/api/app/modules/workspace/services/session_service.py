"""Minimal ephemeral session handling for the Phase 0 workspace."""

from __future__ import annotations

import uuid

from app.modules.workspace.schemas.response import WorkspaceRetention, WorkspaceSchemaModel


class WorkspaceSessionState(WorkspaceSchemaModel):
    session_id: uuid.UUID
    retention: WorkspaceRetention


class WorkspaceSessionService:
    def begin_turn(self, session_id: uuid.UUID | None) -> WorkspaceSessionState:
        return WorkspaceSessionState(
            session_id=session_id or uuid.uuid4(),
            retention=WorkspaceRetention(retention_class="ephemeral"),
        )
