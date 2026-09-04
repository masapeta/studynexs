"""Bounded Phase 0 registry for teacher workspace read tools."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Awaitable, Callable, Mapping

from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.models.audit import AuditLog
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext, WorkspaceToolMetadata

APPROVED_WORKSPACE_TOOL_NAMES = frozenset(
    {
        "resolve_student_in_teacher_scope",
        "get_student_learning_evidence_report",
        "get_teacher_navigation_targets",
    }
)
_TRANSIENT_TOOL_ERRORS = (asyncio.TimeoutError, ConnectionError, OSError)


class WorkspaceToolRegistryError(ValueError):
    """Base error for the bounded workspace tool registry."""


class WorkspaceToolNotFoundError(WorkspaceToolRegistryError):
    """Raised when a caller asks for an unregistered tool."""


class WorkspaceToolValidationError(WorkspaceToolRegistryError):
    """Raised when a tool input or output violates its contract."""


class WorkspaceToolExecutionError(WorkspaceToolRegistryError):
    """Raised when a tool cannot complete within its bounded runtime policy."""


class WorkspaceToolCircuitOpenError(WorkspaceToolRegistryError):
    """Raised when a tool is temporarily blocked after repeated failures."""


WorkspaceToolHandler = Callable[
    [AsyncSession, WorkspaceToolContext, BaseModel], Awaitable[BaseModel]
]


@dataclass(frozen=True)
class RegisteredWorkspaceTool:
    """Static registry entry for a single bounded workspace tool."""

    metadata: WorkspaceToolMetadata
    handler: WorkspaceToolHandler


@dataclass
class _CircuitState:
    consecutive_failures: int = 0
    opened_until: float = 0.0


@dataclass
class WorkspaceToolRegistry:
    """Read-only registry and executor for the approved Phase 0 tools."""

    _tools: Mapping[str, RegisteredWorkspaceTool]
    _clock: Callable[[], float] = time.monotonic
    _circuit_state: dict[str, _CircuitState] = field(default_factory=dict)

    @classmethod
    def load_default(cls, *, settings: Settings | None = None) -> "WorkspaceToolRegistry":
        from app.modules.ai.orchestration.tools.read.get_student_learning_evidence_report import (
            TOOL_HANDLER as REPORT_TOOL_HANDLER,
        )
        from app.modules.ai.orchestration.tools.read.get_student_learning_evidence_report import (
            TOOL_METADATA as REPORT_TOOL_METADATA,
        )
        from app.modules.ai.orchestration.tools.read.get_teacher_navigation_targets import (
            TOOL_HANDLER as NAV_TOOL_HANDLER,
        )
        from app.modules.ai.orchestration.tools.read.get_teacher_navigation_targets import (
            TOOL_METADATA as NAV_TOOL_METADATA,
        )
        from app.modules.ai.orchestration.tools.read.resolve_student_in_teacher_scope import (
            TOOL_HANDLER as RESOLVE_TOOL_HANDLER,
        )
        from app.modules.ai.orchestration.tools.read.resolve_student_in_teacher_scope import (
            TOOL_METADATA as RESOLVE_TOOL_METADATA,
        )

        runtime = settings or get_settings()

        return cls.from_tools(
            (
                RegisteredWorkspaceTool(
                    metadata=cls._apply_runtime_settings(RESOLVE_TOOL_METADATA, runtime),
                    handler=RESOLVE_TOOL_HANDLER,
                ),
                RegisteredWorkspaceTool(
                    metadata=cls._apply_runtime_settings(REPORT_TOOL_METADATA, runtime),
                    handler=REPORT_TOOL_HANDLER,
                ),
                RegisteredWorkspaceTool(
                    metadata=cls._apply_runtime_settings(NAV_TOOL_METADATA, runtime),
                    handler=NAV_TOOL_HANDLER,
                ),
            )
        )

    @classmethod
    def from_tools(
        cls,
        tools: tuple[RegisteredWorkspaceTool, ...],
        *,
        strict_approved_names: bool = True,
        clock: Callable[[], float] | None = None,
    ) -> "WorkspaceToolRegistry":
        by_name: dict[str, RegisteredWorkspaceTool] = {}
        for tool in tools:
            name = tool.metadata.name
            if name in by_name:
                raise WorkspaceToolRegistryError(f"Duplicate workspace tool registration: {name}")
            if strict_approved_names and name not in APPROVED_WORKSPACE_TOOL_NAMES:
                raise WorkspaceToolRegistryError(f"Unapproved workspace tool registration: {name}")
            by_name[name] = tool

        if strict_approved_names and set(by_name) != APPROVED_WORKSPACE_TOOL_NAMES:
            missing = sorted(APPROVED_WORKSPACE_TOOL_NAMES - set(by_name))
            extra = sorted(set(by_name) - APPROVED_WORKSPACE_TOOL_NAMES)
            fragments: list[str] = []
            if missing:
                fragments.append(f"missing={missing}")
            if extra:
                fragments.append(f"extra={extra}")
            detail = ", ".join(fragments) or "approved tool set mismatch"
            raise WorkspaceToolRegistryError(
                f"Workspace tool registry must expose exactly the approved Phase 0 tools ({detail})"
            )

        for tool in by_name.values():
            cls._validate_metadata(tool.metadata)

        return cls(
            _tools=MappingProxyType(by_name),
            _clock=clock or time.monotonic,
        )

    @staticmethod
    def _validate_metadata(metadata: WorkspaceToolMetadata) -> None:
        if not issubclass(metadata.input_schema, BaseModel):
            raise WorkspaceToolRegistryError(
                f"Tool input schema must be a Pydantic model: {metadata.name}"
            )
        if not issubclass(metadata.output_schema, BaseModel):
            raise WorkspaceToolRegistryError(
                f"Tool output schema must be a Pydantic model: {metadata.name}"
            )

    @staticmethod
    def _apply_runtime_settings(
        metadata: WorkspaceToolMetadata,
        settings: Settings,
    ) -> WorkspaceToolMetadata:
        return metadata.model_copy(
            update={
                "timeout_ms": min(metadata.timeout_ms, settings.WORKSPACE_TOOL_TIMEOUT_MS),
                "retry_count": min(metadata.retry_count, settings.WORKSPACE_TOOL_READ_RETRY_COUNT),
                "circuit_breaker_threshold": settings.WORKSPACE_TOOL_CIRCUIT_BREAKER_THRESHOLD,
                "circuit_breaker_cooldown_seconds": (
                    settings.WORKSPACE_TOOL_CIRCUIT_BREAKER_COOLDOWN_SECONDS
                ),
            }
        )

    def definitions(self) -> tuple[WorkspaceToolMetadata, ...]:
        return tuple(tool.metadata for tool in self._tools.values())

    def names(self) -> tuple[str, ...]:
        return tuple(self._tools.keys())

    def get(self, name: str) -> RegisteredWorkspaceTool:
        tool = self._tools.get(name)
        if tool is None:
            raise WorkspaceToolNotFoundError(f"Workspace tool not found: {name}")
        return tool

    async def execute(
        self,
        name: str,
        *,
        db: AsyncSession,
        context: WorkspaceToolContext,
        payload: dict[str, Any] | BaseModel,
    ) -> BaseModel:
        tool = self.get(name)
        metadata = tool.metadata

        if context.role not in metadata.allowed_roles:
            await self._audit_tool_event(
                db=db,
                context=context,
                metadata=metadata,
                outcome="role_denied",
            )
            raise WorkspaceToolExecutionError(
                f"Role {context.role!r} is not allowed to execute {name}"
            )

        try:
            self._ensure_circuit_closed(name)
        except WorkspaceToolCircuitOpenError:
            await self._audit_tool_event(
                db=db,
                context=context,
                metadata=metadata,
                outcome="circuit_open",
            )
            raise

        try:
            input_model = self._validate_input(metadata, payload)
        except WorkspaceToolValidationError:
            await self._audit_tool_event(
                db=db,
                context=context,
                metadata=metadata,
                outcome="invalid_input",
            )
            raise

        attempts = metadata.retry_count + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                result = await asyncio.wait_for(
                    tool.handler(db, context, input_model),
                    timeout=metadata.timeout_ms / 1000,
                )
                validated = metadata.output_schema.model_validate(result)
                self._reset_circuit(name)
                await self._audit_tool_event(
                    db=db,
                    context=context,
                    metadata=metadata,
                    outcome="success",
                    attempt_count=attempt + 1,
                )
                return validated
            except ValidationError as exc:
                self._record_failure(name, metadata)
                await self._audit_tool_event(
                    db=db,
                    context=context,
                    metadata=metadata,
                    outcome="invalid_output",
                    attempt_count=attempt + 1,
                    error_type=exc.__class__.__name__,
                )
                raise WorkspaceToolValidationError(
                    f"Workspace tool {name} returned an invalid payload"
                ) from exc
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                is_transient = isinstance(exc, _TRANSIENT_TOOL_ERRORS)
                if is_transient and attempt + 1 < attempts:
                    continue
                self._record_failure(name, metadata)
                await self._audit_tool_event(
                    db=db,
                    context=context,
                    metadata=metadata,
                    outcome="execution_failed",
                    attempt_count=attempt + 1,
                    error_type=exc.__class__.__name__,
                )
                raise WorkspaceToolExecutionError(
                    f"Workspace tool {name} failed: {exc}"
                ) from exc

        self._record_failure(name, metadata)
        await self._audit_tool_event(
            db=db,
            context=context,
            metadata=metadata,
            outcome="execution_failed",
            attempt_count=attempts,
            error_type=last_error.__class__.__name__ if last_error is not None else None,
        )
        raise WorkspaceToolExecutionError(
            f"Workspace tool {name} failed without returning a result"
        ) from last_error

    def _validate_input(
        self,
        metadata: WorkspaceToolMetadata,
        payload: dict[str, Any] | BaseModel,
    ) -> BaseModel:
        try:
            input_model = metadata.input_schema.model_validate(payload)
        except ValidationError as exc:
            raise WorkspaceToolValidationError(
                f"Workspace tool {metadata.name} received an invalid input payload"
            ) from exc

        payload_size = len(json.dumps(input_model.model_dump(mode="json")))
        if payload_size > metadata.max_payload_size:
            raise WorkspaceToolValidationError(
                f"Workspace tool {metadata.name} payload exceeded max size"
            )
        return input_model

    def _ensure_circuit_closed(self, name: str) -> None:
        state = self._circuit_state.get(name)
        if state is None:
            return
        if state.opened_until > self._clock():
            raise WorkspaceToolCircuitOpenError(
                f"Workspace tool circuit is open for {name}"
            )
        if state.opened_until:
            state.consecutive_failures = 0
            state.opened_until = 0.0

    def _record_failure(self, name: str, metadata: WorkspaceToolMetadata) -> None:
        state = self._circuit_state.setdefault(name, _CircuitState())
        state.consecutive_failures += 1
        if state.consecutive_failures >= metadata.circuit_breaker_threshold:
            state.opened_until = self._clock() + metadata.circuit_breaker_cooldown_seconds

    def _reset_circuit(self, name: str) -> None:
        state = self._circuit_state.get(name)
        if state is None:
            return
        state.consecutive_failures = 0
        state.opened_until = 0.0

    async def _audit_tool_event(
        self,
        *,
        db: AsyncSession,
        context: WorkspaceToolContext,
        metadata: WorkspaceToolMetadata,
        outcome: str,
        attempt_count: int | None = None,
        error_type: str | None = None,
    ) -> None:
        details: dict[str, Any] = {
            "tool_name": metadata.name,
            "outcome": outcome,
            "correlation_id": context.correlation_id,
            "read_only": metadata.read_only,
            "side_effect_level": metadata.side_effect_level,
            "pii_level": metadata.pii_level,
            "scope_rule": metadata.scope_rule,
            "tool_result_cache_policy": metadata.tool_result_cache_policy,
            "timeout_ms": metadata.timeout_ms,
            "retry_count": metadata.retry_count,
        }
        if attempt_count is not None:
            details["attempt_count"] = attempt_count
        if error_type is not None:
            details["error_type"] = error_type

        db.add(
            AuditLog(
                school_id=context.school_id,
                user_id=context.teacher_user_id,
                action=metadata.audit_event_type,
                resource_type="workspace_tool",
                resource_id=metadata.name[:50],
                details=details,
            )
        )
        await db.flush()
