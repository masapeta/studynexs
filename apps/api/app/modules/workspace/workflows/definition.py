"""WorkflowDefinition — the minimal production contract for a first-class workflow.

Metadata over existing governed services (like `CapabilityContract`), NOT an engine. A
definition declares WHAT a workflow is and its governance envelope; it does not contain
execution code. The deterministic executor (Phase 4) and any future agentic executor consume
this contract; the planner/router never inspects `execution_mode`.

Design choices grounded in the repo:
* Input/output contracts REFERENCE existing Pydantic schemas (e.g. QP's `GenerateRequest`)
  rather than duplicating them — the workflow validates through the domain's own schema.
* Authorization is declared as required role names and REUSES the existing authorization
  service at execution time; this contract does not implement a second authz engine.
* Approval is a boolean envelope flag; the authoritative approval RULES stay in the domain
  (QP's `assert_qp_approve`, `PaperStatus`). The workflow layer orchestrates, it does not
  re-decide who may approve.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from pydantic import BaseModel


class ExecutionMode(str, enum.Enum):
    """How a workflow is executed. `AGENTIC` is an architectural option; only `DETERMINISTIC`
    is implemented in this phase. The routing layer must not depend on this value."""

    DETERMINISTIC = "deterministic"
    AGENTIC = "agentic"


@dataclass(frozen=True)
class WorkflowIO:
    """Typed input/output boundary. Points at existing domain schemas; does not redefine them."""

    input_schema: type[BaseModel]
    output_schema: type[BaseModel]


@dataclass(frozen=True)
class WorkflowDefinition:
    """The smallest production-grade workflow contract the StudyNexs roadmap needs."""

    workflow_id: str                         # stable id the planner routes to (e.g. question_paper)
    version: str                             # semantic version of THIS workflow contract
    name: str                                # human label
    description: str
    io: WorkflowIO
    execution_mode: ExecutionMode = ExecutionMode.DETERMINISTIC
    # Authorization envelope — enforced by the EXISTING authz service at execution time.
    required_roles: tuple[str, ...] = ()
    # Approval envelope — the domain owns the actual approval rules/lifecycle.
    approval_required: bool = False
    # Whether a run is expected to execute on the existing Arq worker (vs. synchronous).
    is_async: bool = False
    # Domain artifact/status this workflow wraps (documentation + audit correlation only).
    domain_resource: str | None = None       # e.g. "question_paper"
    audit_action: str | None = None          # audit_logs.action, e.g. "workflow.question_paper"
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.workflow_id or not self.workflow_id.isidentifier():
            raise ValueError(f"workflow_id must be a valid identifier: {self.workflow_id!r}")
        if not self.version:
            raise ValueError(f"workflow {self.workflow_id} requires a version")
        in_schema = self.io.input_schema
        out_schema = self.io.output_schema
        if not (isinstance(in_schema, type) and issubclass(in_schema, BaseModel)):
            raise ValueError(f"workflow {self.workflow_id} input_schema must be a Pydantic model")
        if not (isinstance(out_schema, type) and issubclass(out_schema, BaseModel)):
            raise ValueError(f"workflow {self.workflow_id} output_schema must be a Pydantic model")
