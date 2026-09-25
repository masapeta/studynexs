"""Production workflow model for the StudyNexs assistant (Phase 3).

A *workflow* is a first-class, multi-step product process (question paper, evaluation, lesson
plan, remediation, parent intervention) — distinct from a single deterministic capability and
from a bounded composition. This package provides only the **contract + lifecycle model**, not
a workflow engine: no DSL, no dynamic graph, no orchestration framework, no agent executor.

It is metadata over the EXISTING governed services and Arq jobs — the same discipline as the
capability contract registry (`assistant.contracts`). Question Paper is validated against this
model here (design-level) and becomes the first real consumer in Phase 4.
"""

from __future__ import annotations

from app.modules.workspace.workflows.definition import (
    ExecutionMode,
    WorkflowDefinition,
    WorkflowIO,
)
from app.modules.workspace.workflows.lifecycle import (
    TERMINAL_STATES,
    WorkflowState,
    can_transition,
    is_terminal,
)
from app.modules.workspace.workflows.registry import (
    get_workflow,
    list_workflows,
    register_workflow,
)

__all__ = [
    "ExecutionMode",
    "WorkflowDefinition",
    "WorkflowIO",
    "WorkflowState",
    "TERMINAL_STATES",
    "can_transition",
    "is_terminal",
    "get_workflow",
    "list_workflows",
    "register_workflow",
]
