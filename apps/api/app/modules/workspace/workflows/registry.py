"""Workflow registry — a small, fail-fast lookup, mirroring the capability contract registry.

This is NOT capability metadata (that stays in `assistant.contracts`) and NOT a second semantic
model (that stays as `PlannerDecision`). It is the minimal map the assistant needs to route a
planner-chosen workflow target to its `WorkflowDefinition`. Registration is validated at import
time so a malformed definition fails before any request.

Question Paper is registered here as the FIRST definition, validated against its real domain
schemas (`GenerateRequest` in, `QuestionPaperOut` out). It is not yet wired into the assistant
dispatch — that is Phase 4. Registering it now proves the generic model represents QP without
touching the QP domain lifecycle.
"""

from __future__ import annotations

from app.modules.workspace.workflows.definition import (
    ExecutionMode,
    WorkflowDefinition,
    WorkflowIO,
)

_REGISTRY: dict[str, WorkflowDefinition] = {}


def register_workflow(definition: WorkflowDefinition) -> None:
    if definition.workflow_id in _REGISTRY:
        raise ValueError(f"workflow already registered: {definition.workflow_id}")
    _REGISTRY[definition.workflow_id] = definition


def get_workflow(workflow_id: str | None) -> WorkflowDefinition | None:
    if not workflow_id:
        return None
    return _REGISTRY.get(workflow_id)


def list_workflows() -> list[WorkflowDefinition]:
    return list(_REGISTRY.values())


def _register_builtin_workflows() -> None:
    """Register the workflows already in product scope. Only QP is contract-validated today;
    the others are added as their real domain schemas/consumers land (Phases 5-7)."""
    # Import domain schemas lazily so the workflow package has no heavy import-time deps.
    from app.modules.ai.schemas.question_paper import GenerateRequest, QuestionPaperOut

    register_workflow(
        WorkflowDefinition(
            workflow_id="question_paper",
            version="1.0",
            name="Question Paper",
            description=(
                "Generate a curriculum-grounded question paper (draft), reviewed and approved "
                "by a teacher/incharge before it carries authority."
            ),
            io=WorkflowIO(input_schema=GenerateRequest, output_schema=QuestionPaperOut),
            execution_mode=ExecutionMode.DETERMINISTIC,
            required_roles=("teacher", "class_incharge", "admin", "super_admin"),
            approval_required=True,
            is_async=False,
            domain_resource="question_paper",
            audit_action="workflow.question_paper",
            tags=("assessment", "generation"),
        )
    )


_register_builtin_workflows()
