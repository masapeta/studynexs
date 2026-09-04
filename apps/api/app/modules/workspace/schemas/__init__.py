"""Workspace request and response contracts for the Phase 0 teacher copilot."""

from app.modules.workspace.schemas.blocks import (
    ActionListBlock,
    CitationListBlock,
    ErrorStateBlock,
    MetricRowBlock,
    StudentCardBlock,
    TableBlock,
    WorkspaceAction,
    WorkspaceBlock,
    WorkspaceCitation,
)
from app.modules.workspace.schemas.request import WorkspaceTurnRequest
from app.modules.workspace.schemas.response import (
    WorkspaceApproval,
    WorkspaceError,
    WorkspaceMessage,
    WorkspaceResponse,
    WorkspaceRetention,
    WorkspaceTelemetry,
    WorkspaceVerification,
    WorkspaceWarning,
)

__all__ = [
    "ActionListBlock",
    "CitationListBlock",
    "ErrorStateBlock",
    "MetricRowBlock",
    "StudentCardBlock",
    "TableBlock",
    "WorkspaceAction",
    "WorkspaceApproval",
    "WorkspaceBlock",
    "WorkspaceCitation",
    "WorkspaceError",
    "WorkspaceMessage",
    "WorkspaceResponse",
    "WorkspaceRetention",
    "WorkspaceTelemetry",
    "WorkspaceTurnRequest",
    "WorkspaceVerification",
    "WorkspaceWarning",
]
