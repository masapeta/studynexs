"""Execute the bounded Phase 0 workspace read-tool sequence."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.orchestration.router import WorkspaceRouteDecision
from app.modules.ai.orchestration.tool_registry import (
    WorkspaceToolRegistry,
    WorkspaceToolRegistryError,
)
from app.modules.ai.orchestration.tool_types import WorkspaceToolContext
from app.modules.ai.orchestration.tools.read.get_student_learning_evidence_report import (
    GetStudentLearningEvidenceReportOutput,
)
from app.modules.ai.orchestration.tools.read.get_teacher_navigation_targets import (
    GetTeacherNavigationTargetsOutput,
)
from app.modules.ai.orchestration.tools.read.resolve_student_in_teacher_scope import (
    ResolveStudentInTeacherScopeOutput,
)
from app.modules.workspace.schemas.response import WorkspaceSchemaModel


class WorkspaceOrchestrationError(RuntimeError):
    def __init__(self, detail: str, *, tool_calls: int, tool_failures: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.tool_calls = tool_calls
        self.tool_failures = tool_failures


class WorkspaceReadOrchestrationResult(WorkspaceSchemaModel):
    route: WorkspaceRouteDecision
    resolve: ResolveStudentInTeacherScopeOutput
    report: GetStudentLearningEvidenceReportOutput | None = None
    navigation: GetTeacherNavigationTargetsOutput | None = None
    tool_calls: int = 0
    tool_failures: int = 0


class WorkspaceReadOrchestrator:
    def __init__(self, registry: WorkspaceToolRegistry, *, max_tool_calls: int) -> None:
        self._registry = registry
        self._max_tool_calls = max_tool_calls

    async def run(
        self,
        *,
        db: AsyncSession,
        context: WorkspaceToolContext,
        route: WorkspaceRouteDecision,
    ) -> WorkspaceReadOrchestrationResult:
        if route.student_selector is None:
            raise WorkspaceOrchestrationError(
                "The deterministic route did not produce a student selector.",
                tool_calls=0,
                tool_failures=0,
            )

        tool_calls = 0
        try:
            resolve = await self._registry.execute(
                "resolve_student_in_teacher_scope",
                db=db,
                context=context,
                payload={"selector": route.student_selector},
            )
            tool_calls += 1
        except WorkspaceToolRegistryError as exc:
            raise WorkspaceOrchestrationError(
                f"Student resolution failed: {exc}",
                tool_calls=tool_calls + 1,
                tool_failures=1,
            ) from exc

        result = WorkspaceReadOrchestrationResult(
            route=route,
            resolve=ResolveStudentInTeacherScopeOutput.model_validate(resolve),
            tool_calls=tool_calls,
        )
        if result.resolve.status != "resolved" or tool_calls >= self._max_tool_calls:
            return result

        student_id = uuid.UUID(result.resolve.student_id)
        try:
            report = await self._registry.execute(
                "get_student_learning_evidence_report",
                db=db,
                context=context,
                payload={"student_id": student_id},
            )
            tool_calls += 1
        except WorkspaceToolRegistryError as exc:
            raise WorkspaceOrchestrationError(
                f"Learning evidence report failed: {exc}",
                tool_calls=tool_calls + 1,
                tool_failures=1,
            ) from exc

        result = result.model_copy(
            update={
                "report": GetStudentLearningEvidenceReportOutput.model_validate(report),
                "tool_calls": tool_calls,
            }
        )
        if tool_calls >= self._max_tool_calls:
            return result

        try:
            navigation = await self._registry.execute(
                "get_teacher_navigation_targets",
                db=db,
                context=context,
                payload={"student_id": student_id},
            )
            tool_calls += 1
        except WorkspaceToolRegistryError as exc:
            raise WorkspaceOrchestrationError(
                f"Navigation target lookup failed: {exc}",
                tool_calls=tool_calls + 1,
                tool_failures=1,
            ) from exc

        return result.model_copy(
            update={
                "navigation": GetTeacherNavigationTargetsOutput.model_validate(navigation),
                "tool_calls": tool_calls,
            }
        )
