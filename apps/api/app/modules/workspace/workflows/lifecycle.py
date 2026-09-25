"""Generic workflow orchestration lifecycle — a small explicit transition model.

This is deliberately NOT a transition engine. It is a fixed, auditable state set with an
explicit allow-list of transitions, mirroring how `Job.status` and `PaperStatus` are modelled
in the codebase (small enums, no framework).

Crucial boundary: this lifecycle tracks ORCHESTRATION/EXECUTION state (is the workflow queued,
running, awaiting approval, done?). It does NOT replace a domain's own business lifecycle. The
Question Paper domain keeps owning `PaperStatus` (DRAFT -> EDITED -> PENDING_APPROVAL ->
APPROVED -> PUBLISHED); the workflow layer merely wraps it (see WORKFLOWS.md §"wraps"). A
workflow carries its domain status alongside this orchestration state; there is no mapping
engine translating one into the other.
"""

from __future__ import annotations

import enum


class WorkflowState(str, enum.Enum):
    """Orchestration state of a workflow run (not the domain's business status)."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES: frozenset[WorkflowState] = frozenset(
    {WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED}
)

# Explicit allow-list. A workflow need not use every state (a synchronous deterministic
# workflow may go CREATED -> RUNNING -> WAITING_FOR_APPROVAL -> COMPLETED and never QUEUE).
_ALLOWED: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.CREATED: frozenset(
        {WorkflowState.QUEUED, WorkflowState.RUNNING, WorkflowState.CANCELLED}
    ),
    WorkflowState.QUEUED: frozenset(
        {WorkflowState.RUNNING, WorkflowState.CANCELLED, WorkflowState.FAILED}
    ),
    WorkflowState.RUNNING: frozenset(
        {
            WorkflowState.WAITING_FOR_INPUT,
            WorkflowState.WAITING_FOR_APPROVAL,
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        }
    ),
    WorkflowState.WAITING_FOR_INPUT: frozenset(
        {WorkflowState.RUNNING, WorkflowState.CANCELLED, WorkflowState.FAILED}
    ),
    WorkflowState.WAITING_FOR_APPROVAL: frozenset(
        # approval -> COMPLETED; rejection loops back to RUNNING (re-work); or cancel.
        {WorkflowState.COMPLETED, WorkflowState.RUNNING, WorkflowState.CANCELLED}
    ),
    WorkflowState.COMPLETED: frozenset(),
    WorkflowState.FAILED: frozenset(),
    WorkflowState.CANCELLED: frozenset(),
}


def is_terminal(state: WorkflowState) -> bool:
    return state in TERMINAL_STATES


def can_transition(src: WorkflowState, dst: WorkflowState) -> bool:
    """True iff the orchestration transition src -> dst is permitted. Terminal states are sinks."""
    return dst in _ALLOWED.get(src, frozenset())
