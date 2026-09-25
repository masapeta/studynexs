"""Phase 3: the production workflow model (contract + lifecycle), and its QP compatibility.

These tests prove the generic workflow model is production-grade and can represent Question
Paper WITHOUT touching the QP domain lifecycle — the Phase 3 exit criterion. They assert the
contract validates, the lifecycle transition allow-list is correct, and QP's real domain
schemas/status/approval map onto the generic model.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.modules.workspace.workflows import (
    TERMINAL_STATES,
    ExecutionMode,
    WorkflowDefinition,
    WorkflowIO,
    WorkflowState,
    can_transition,
    get_workflow,
    is_terminal,
    list_workflows,
)


class _In(BaseModel):
    x: int


class _Out(BaseModel):
    y: int


# ── WorkflowDefinition validation ─────────────────────────────────────────────


def test_definition_accepts_valid_contract():
    wf = WorkflowDefinition(
        workflow_id="demo",
        version="1.0",
        name="Demo",
        description="d",
        io=WorkflowIO(input_schema=_In, output_schema=_Out),
    )
    assert wf.execution_mode is ExecutionMode.DETERMINISTIC  # default
    assert wf.approval_required is False
    assert wf.io.input_schema is _In


def test_definition_rejects_bad_workflow_id():
    with pytest.raises(ValueError):
        WorkflowDefinition(
            workflow_id="not an identifier",
            version="1.0",
            name="x",
            description="d",
            io=WorkflowIO(input_schema=_In, output_schema=_Out),
        )


def test_definition_requires_version():
    with pytest.raises(ValueError):
        WorkflowDefinition(
            workflow_id="demo",
            version="",
            name="x",
            description="d",
            io=WorkflowIO(input_schema=_In, output_schema=_Out),
        )


def test_definition_rejects_non_pydantic_io():
    class NotAModel:
        pass

    with pytest.raises(ValueError):
        WorkflowDefinition(
            workflow_id="demo",
            version="1.0",
            name="x",
            description="d",
            io=WorkflowIO(input_schema=NotAModel, output_schema=_Out),  # type: ignore[arg-type]
        )


def test_execution_mode_supports_both_but_defaults_deterministic():
    assert {m.value for m in ExecutionMode} == {"deterministic", "agentic"}
    wf = WorkflowDefinition(
        workflow_id="future",
        version="1.0",
        name="Future",
        description="d",
        io=WorkflowIO(input_schema=_In, output_schema=_Out),
        execution_mode=ExecutionMode.AGENTIC,
    )
    assert wf.execution_mode is ExecutionMode.AGENTIC


# ── Lifecycle transitions ─────────────────────────────────────────────────────


def test_valid_transitions():
    assert can_transition(WorkflowState.CREATED, WorkflowState.RUNNING)
    assert can_transition(WorkflowState.CREATED, WorkflowState.QUEUED)
    assert can_transition(WorkflowState.QUEUED, WorkflowState.RUNNING)
    assert can_transition(WorkflowState.RUNNING, WorkflowState.WAITING_FOR_APPROVAL)
    assert can_transition(WorkflowState.WAITING_FOR_APPROVAL, WorkflowState.COMPLETED)
    # rejection loops back to RUNNING for re-work
    assert can_transition(WorkflowState.WAITING_FOR_APPROVAL, WorkflowState.RUNNING)


def test_invalid_transitions_rejected():
    assert not can_transition(WorkflowState.CREATED, WorkflowState.COMPLETED)
    assert not can_transition(WorkflowState.COMPLETED, WorkflowState.RUNNING)
    assert not can_transition(WorkflowState.WAITING_FOR_APPROVAL, WorkflowState.QUEUED)


def test_terminal_states_are_sinks():
    for term in (WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED):
        assert is_terminal(term)
        for dst in WorkflowState:
            assert not can_transition(term, dst)
    assert not is_terminal(WorkflowState.RUNNING)


def test_cancellation_reachable_from_active_states():
    for src in (
        WorkflowState.CREATED,
        WorkflowState.QUEUED,
        WorkflowState.RUNNING,
        WorkflowState.WAITING_FOR_INPUT,
        WorkflowState.WAITING_FOR_APPROVAL,
    ):
        assert can_transition(src, WorkflowState.CANCELLED)


def test_failure_reachable_from_execution_states():
    for src in (
        WorkflowState.QUEUED,
        WorkflowState.RUNNING,
        WorkflowState.WAITING_FOR_INPUT,
    ):
        assert can_transition(src, WorkflowState.FAILED)


def test_terminal_set_membership():
    assert TERMINAL_STATES == {
        WorkflowState.COMPLETED,
        WorkflowState.FAILED,
        WorkflowState.CANCELLED,
    }


# ── Registry + Question Paper compatibility (the Phase 3 gate) ─────────────────


def test_question_paper_is_registered():
    wf = get_workflow("question_paper")
    assert wf is not None
    assert wf.workflow_id == "question_paper"
    assert wf.version
    assert wf.name == "Question Paper"


def test_unknown_workflow_returns_none():
    assert get_workflow("does_not_exist") is None
    assert get_workflow(None) is None


def test_question_paper_uses_real_domain_schemas_not_duplicates():
    from app.modules.ai.schemas.question_paper import GenerateRequest, QuestionPaperOut

    wf = get_workflow("question_paper")
    assert wf is not None
    # The workflow REFERENCES QP's own schemas — no duplicate QP schema was created.
    assert wf.io.input_schema is GenerateRequest
    assert wf.io.output_schema is QuestionPaperOut


def test_question_paper_declares_deterministic_and_approval():
    wf = get_workflow("question_paper")
    assert wf is not None
    assert wf.execution_mode is ExecutionMode.DETERMINISTIC
    assert wf.approval_required is True  # QP requires human approval before it carries authority
    assert wf.domain_resource == "question_paper"
    assert wf.audit_action  # auditable


def test_question_paper_authorization_matches_domain_roles():
    """The workflow declares the roles the EXISTING QP endpoints gate on; it does not invent a
    second authz model. QP submit/approve use teacher/incharge (+admin)."""
    wf = get_workflow("question_paper")
    assert wf is not None
    assert "teacher" in wf.required_roles
    assert "class_incharge" in wf.required_roles


def test_generic_lifecycle_wraps_qp_domain_lifecycle_without_owning_it():
    """QP keeps PaperStatus as its authoritative business lifecycle; the generic orchestration
    lifecycle merely wraps it. This asserts the two are DISTINCT (no rewrite, no mapping engine):
    the workflow model must not import or redefine PaperStatus."""
    from app.db.models.question_paper import PaperStatus

    # QP's business statuses are unchanged and independent of WorkflowState.
    assert PaperStatus.PENDING_APPROVAL.value == "pending_approval"
    assert PaperStatus.APPROVED.value == "approved"
    # The orchestration state that corresponds to QP awaiting sign-off exists generically,
    # but it is a SEPARATE concept (different type, different values namespace).
    assert WorkflowState.WAITING_FOR_APPROVAL.value == "waiting_for_approval"
    assert not isinstance(PaperStatus.APPROVED, WorkflowState)


def test_registry_has_no_duplicate_ids():
    ids = [w.workflow_id for w in list_workflows()]
    assert len(ids) == len(set(ids))
