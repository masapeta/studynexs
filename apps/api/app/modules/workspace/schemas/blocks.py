"""Typed workspace blocks for the Phase 0 teacher copilot."""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceSchemaModel(BaseModel):
    """Shared strict base for workspace contracts."""

    model_config = ConfigDict(extra="forbid")


WorkspaceBlockPriority: TypeAlias = Literal["primary", "secondary"]
WorkspaceMetricStatus: TypeAlias = Literal["normal", "warning", "risk"]
WorkspaceActionType: TypeAlias = Literal["navigate"]
WorkspaceTableCell: TypeAlias = str | int | float | bool | None


class WorkspaceCitation(WorkspaceSchemaModel):
    label: str
    source_type: str
    source_id: str
    summary: str


class WorkspaceAction(WorkspaceSchemaModel):
    label: str
    action_type: WorkspaceActionType = "navigate"
    href: str
    permission_gate: str
    enabled: bool = True


class StudentCardPayload(WorkspaceSchemaModel):
    student_id: str
    display_name: str
    class_label: str
    section_label: str
    admission_no: str | None


class WorkspaceMetricItem(WorkspaceSchemaModel):
    label: str
    value: str | int | float
    status: WorkspaceMetricStatus


class MetricRowPayload(WorkspaceSchemaModel):
    items: list[WorkspaceMetricItem] = Field(default_factory=list)


class WorkspaceTableColumn(WorkspaceSchemaModel):
    key: str
    label: str


class TablePayload(WorkspaceSchemaModel):
    columns: list[WorkspaceTableColumn] = Field(default_factory=list)
    rows: list[dict[str, WorkspaceTableCell]] = Field(default_factory=list)
    empty_message: str


class CitationListPayload(WorkspaceSchemaModel):
    items: list[WorkspaceCitation] = Field(default_factory=list)


class ActionListPayload(WorkspaceSchemaModel):
    items: list[WorkspaceAction] = Field(default_factory=list)


class ErrorStatePayload(WorkspaceSchemaModel):
    code: str
    headline: str
    detail: str
    retryable: bool = False


class WorkspaceBlockBase(WorkspaceSchemaModel):
    id: str
    title: str | None = None
    priority: WorkspaceBlockPriority


class StudentCardBlock(WorkspaceBlockBase):
    type: Literal["student_card"] = "student_card"
    payload: StudentCardPayload


class MetricRowBlock(WorkspaceBlockBase):
    type: Literal["metric_row"] = "metric_row"
    payload: MetricRowPayload


class TableBlock(WorkspaceBlockBase):
    type: Literal["table"] = "table"
    payload: TablePayload


class CitationListBlock(WorkspaceBlockBase):
    type: Literal["citation_list"] = "citation_list"
    payload: CitationListPayload


class ActionListBlock(WorkspaceBlockBase):
    type: Literal["action_list"] = "action_list"
    payload: ActionListPayload


class ErrorStateBlock(WorkspaceBlockBase):
    type: Literal["error_state"] = "error_state"
    payload: ErrorStatePayload


WorkspaceBlock = Annotated[
    StudentCardBlock
    | MetricRowBlock
    | TableBlock
    | CitationListBlock
    | ActionListBlock
    | ErrorStateBlock,
    Field(discriminator="type"),
]
