"""Schemas for platform engineering endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class ModuleDependencyOut(BaseModel):
    satisfied: list[str] = Field(default_factory=list)
    pending: list[str] = Field(default_factory=list)


class EngineeringModuleOut(BaseModel):
    id: str
    name: str
    status: str
    verified: str = "not_started"
    batch: int | None = None
    doc: str = ""
    depends_on: ModuleDependencyOut = Field(default_factory=ModuleDependencyOut)


class NextMilestoneOut(BaseModel):
    batch: int | None = None
    title: str = ""
    summary: str = ""
    estimated_days: int | None = None
    dependencies_blocking: list[str] = Field(default_factory=list)
    dependencies_satisfied: list[str] = Field(default_factory=list)
    dependencies_optional: list[str] = Field(default_factory=list)


class EngineeringStatusOut(BaseModel):
    schema_version: int = 3
    architecture_version: str = "unknown"
    updated_at: str = ""
    last_engineering_batch: int | None = None
    branch: str = ""
    last_commit: str = ""
    last_completed_batch: str | None = None
    current_batch: str | None = None
    next_batch: str | None = None
    next_milestone: NextMilestoneOut | None = None
    tests: dict[str, Any] = Field(default_factory=dict)
    providers: dict[str, str] = Field(default_factory=dict)
    capability_matrix: list[dict[str, Any]] = Field(default_factory=list)
    modules: list[EngineeringModuleOut] = Field(default_factory=list)
    roadmap: dict[str, Any] = Field(default_factory=dict)
    doc_links: dict[str, str] = Field(default_factory=dict)
    runtime: dict[str, str | None] = Field(default_factory=dict)
