"""Convert workspace routing and tool outputs into the response envelope."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.modules.ai.orchestration.orchestrator import WorkspaceReadOrchestrationResult
from app.modules.ai.orchestration.router import WorkspaceRouteDecision
from app.modules.workspace.schemas.blocks import (
    ActionListBlock,
    ActionListPayload,
    CitationListBlock,
    CitationListPayload,
    ErrorStateBlock,
    ErrorStatePayload,
    MetricRowBlock,
    StudentCardBlock,
    TableBlock,
    TablePayload,
    WorkspaceAction,
)
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

_NO_REPORT_SUMMARY = (
    "Teacher Copilot currently supports one grounded student learning evidence report at a time."
)


def _base_response(
    *,
    request_id: uuid.UUID,
    correlation_id: str,
    message: WorkspaceMessage,
    verification: WorkspaceVerification,
    tool_calls: int,
    tool_failures: int,
    retention: WorkspaceRetention,
    warnings: list[WorkspaceWarning] | None = None,
    errors: list[WorkspaceError] | None = None,
    blocks: list[object] | None = None,
    citations: list[object] | None = None,
    actions: list[WorkspaceAction] | None = None,
) -> WorkspaceResponse:
    return WorkspaceResponse(
        request_id=request_id,
        correlation_id=correlation_id,
        message=message,
        blocks=list(blocks or []),
        citations=list(citations or []),
        actions=list(actions or []),
        verification=verification,
        warnings=list(warnings or []),
        errors=list(errors or []),
        approval=WorkspaceApproval(required=False, reason=None),
        data_retention=retention,
        speech=None,
        telemetry=WorkspaceTelemetry(
            used_model=None,
            used_fallback=False,
            tool_calls=tool_calls,
            tool_failures=tool_failures,
        ),
    )


def _unsupported_route_warning(route: WorkspaceRouteDecision) -> list[WorkspaceWarning]:
    if route.strategy == "local_model":
        return [
            WorkspaceWarning(
                code="model_routing_deferred",
                detail=(
                    "Model-assisted normalization is enabled by policy but not "
                    "exercised by this first deterministic slice."
                ),
            )
        ]
    if route.strategy == "cloud_fallback":
        return [
            WorkspaceWarning(
                code="cloud_fallback_deferred",
                detail=(
                    "Cloud fallback is enabled by policy but this slice only serves "
                    "deterministic read responses."
                ),
            )
        ]
    return []


def build_unsupported_request_response(
    *,
    request_id: uuid.UUID,
    correlation_id: str,
    route: WorkspaceRouteDecision,
    retention: WorkspaceRetention,
) -> WorkspaceResponse:
    detail = route.detail or _NO_REPORT_SUMMARY
    return _base_response(
        request_id=request_id,
        correlation_id=correlation_id,
        message=WorkspaceMessage(
            title="Request not supported yet",
            summary=_NO_REPORT_SUMMARY,
            tone="blocked",
        ),
        verification=WorkspaceVerification(
            status="missing",
            checked_at=None,
            source_systems=[],
        ),
        tool_calls=0,
        tool_failures=0,
        retention=retention,
        warnings=_unsupported_route_warning(route),
        errors=[WorkspaceError(code="unsupported_request", detail=detail)],
        blocks=[
            ErrorStateBlock(
                id="workspace-unsupported-request",
                type="error_state",
                title="Teacher Copilot is still bounded",
                priority="primary",
                payload=ErrorStatePayload(
                    code="unsupported_request",
                    headline="Only student learning evidence requests are available in this slice.",
                    detail=detail,
                    retryable=False,
                ),
            )
        ],
    )


def build_tool_failure_response(
    *,
    request_id: uuid.UUID,
    correlation_id: str,
    detail: str,
    tool_calls: int,
    tool_failures: int,
    retention: WorkspaceRetention,
) -> WorkspaceResponse:
    return _base_response(
        request_id=request_id,
        correlation_id=correlation_id,
        message=WorkspaceMessage(
            title="Workspace request could not complete",
            summary=(
                "The request was understood, but the bounded read path failed "
                "before it could return a verified answer."
            ),
            tone="blocked",
        ),
        verification=WorkspaceVerification(
            status="missing",
            checked_at=datetime.now(timezone.utc),
            source_systems=[],
        ),
        tool_calls=tool_calls,
        tool_failures=tool_failures,
        retention=retention,
        errors=[WorkspaceError(code="tool_execution_failed", detail=detail)],
        blocks=[
            ErrorStateBlock(
                id="workspace-tool-failure",
                type="error_state",
                title="Temporary workspace failure",
                priority="primary",
                payload=ErrorStatePayload(
                    code="tool_execution_failed",
                    headline="A bounded read tool failed before the report could be assembled.",
                    detail=detail,
                    retryable=True,
                ),
            )
        ],
    )


def _candidate_table(payload: WorkspaceReadOrchestrationResult) -> TableBlock:
    rows = [candidate.model_dump(mode="json") for candidate in payload.resolve.matches]
    return TableBlock(
        id="workspace-student-candidates",
        type="table",
        title="Matching students",
        priority="primary",
        payload=TablePayload(
            columns=[
                {"key": "display_name", "label": "Student"},
                {"key": "class_label", "label": "Class"},
                {"key": "section_label", "label": "Section"},
                {"key": "admission_no", "label": "Admission no."},
            ],
            rows=rows,
            empty_message="No candidate matches were available.",
        ),
    )


def _resolution_error_code(status: str) -> str:
    if status == "ambiguous":
        return "student_selector_ambiguous"
    if status == "forbidden":
        return "student_out_of_scope"
    return "student_not_found"


def _resolution_error_headline(status: str) -> str:
    if status == "ambiguous":
        return "Multiple students matched that request."
    if status == "forbidden":
        return "The matched student is outside your teaching scope."
    return "No student matched that request."


def build_read_response(
    *,
    request_id: uuid.UUID,
    correlation_id: str,
    result: WorkspaceReadOrchestrationResult,
    retention: WorkspaceRetention,
) -> WorkspaceResponse:
    if result.resolve.status != "resolved":
        code = _resolution_error_code(result.resolve.status)
        detail = result.resolve.detail or _resolution_error_headline(result.resolve.status)
        blocks: list[object] = [
            ErrorStateBlock(
                id="workspace-student-resolution",
                type="error_state",
                title="Student resolution",
                priority="primary",
                payload=ErrorStatePayload(
                    code=code,
                    headline=_resolution_error_headline(result.resolve.status),
                    detail=detail,
                    retryable=result.resolve.status == "ambiguous",
                ),
            )
        ]
        if result.resolve.status == "ambiguous":
            blocks.append(_candidate_table(result))
        return _base_response(
            request_id=request_id,
            correlation_id=correlation_id,
            message=WorkspaceMessage(
                title="Need a clearer student selector",
                summary=detail,
                tone="cautious" if result.resolve.status == "ambiguous" else "blocked",
            ),
            verification=WorkspaceVerification(
                status="missing",
                checked_at=None,
                source_systems=[],
            ),
            tool_calls=result.tool_calls,
            tool_failures=result.tool_failures,
            retention=retention,
            errors=[WorkspaceError(code=code, detail=detail)],
            blocks=blocks,
        )

    report = result.report
    navigation = result.navigation
    actions = navigation.actions if navigation and navigation.status == "ok" else []
    blocks: list[object] = []
    if report and report.student is not None:
        blocks.append(
            StudentCardBlock(
                id="workspace-student-card",
                type="student_card",
                title="Student",
                priority="primary",
                payload=report.student,
            )
        )

    if report is None:
        detail = (
            "The student was resolved, but the workspace did not receive a learning "
            "evidence report."
        )
        blocks.append(
            ErrorStateBlock(
                id="workspace-report-missing",
                type="error_state",
                title="Learning evidence",
                priority="primary",
                payload=ErrorStatePayload(
                    code="report_missing",
                    headline="No learning evidence report was returned.",
                    detail=detail,
                    retryable=True,
                ),
            )
        )
        if actions:
            blocks.append(
                ActionListBlock(
                    id="workspace-navigation-actions",
                    type="action_list",
                    title="Available screens",
                    priority="secondary",
                    payload=ActionListPayload(items=actions),
                )
            )
        return _base_response(
            request_id=request_id,
            correlation_id=correlation_id,
            message=WorkspaceMessage(
                title="Learning evidence unavailable",
                summary=detail,
                tone="blocked",
            ),
            verification=WorkspaceVerification(
                status="missing",
                checked_at=datetime.now(timezone.utc),
                source_systems=[],
            ),
            tool_calls=result.tool_calls,
            tool_failures=result.tool_failures,
            retention=retention,
            errors=[WorkspaceError(code="report_missing", detail=detail)],
            blocks=blocks,
            actions=actions,
        )

    verification = WorkspaceVerification(
        status=report.verification_status,
        checked_at=report.checked_at,
        source_systems=["mastery_service", "exam_service", "knowledge_graph"],
    )
    warnings: list[WorkspaceWarning] = []
    errors: list[WorkspaceError] = []

    if report.status == "ok":
        if report.summary_metrics is not None:
            blocks.append(
                MetricRowBlock(
                    id="workspace-summary-metrics",
                    type="metric_row",
                    title="Learning evidence summary",
                    priority="primary",
                    payload=report.summary_metrics,
                )
            )
        if report.weak_concepts is not None:
            blocks.append(
                TableBlock(
                    id="workspace-weak-concepts",
                    type="table",
                    title="Weak concepts",
                    priority="primary",
                    payload=report.weak_concepts,
                )
            )
        if report.recent_assessment_evidence is not None:
            blocks.append(
                TableBlock(
                    id="workspace-recent-assessments",
                    type="table",
                    title="Recent assessment evidence",
                    priority="secondary",
                    payload=report.recent_assessment_evidence,
                )
            )
        if report.citations:
            blocks.append(
                CitationListBlock(
                    id="workspace-citations",
                    type="citation_list",
                    title="Evidence links",
                    priority="secondary",
                    payload=CitationListPayload(items=report.citations),
                )
            )
        if actions:
            blocks.append(
                ActionListBlock(
                    id="workspace-navigation-actions",
                    type="action_list",
                    title="Continue in teaching tools",
                    priority="secondary",
                    payload=ActionListPayload(items=actions),
                )
            )
        if report.verification_status != "verified":
            warnings.append(
                WorkspaceWarning(
                    code=f"verification_{report.verification_status}",
                    detail=(
                        "The report is renderable, but its evidence chain is not fully "
                        "grounded."
                    ),
                )
            )
        weak_count = len(report.weak_concepts.rows) if report.weak_concepts is not None else 0
        assessment_count = (
            len(report.recent_assessment_evidence.rows)
            if report.recent_assessment_evidence is not None
            else 0
        )
        summary = (
            f"{report.student.display_name} has {weak_count} weak concepts linked to "
            f"{assessment_count} recent assessments."
        )
        return _base_response(
            request_id=request_id,
            correlation_id=correlation_id,
            message=WorkspaceMessage(
                title="Student learning evidence report",
                summary=summary,
                tone="informative",
            ),
            verification=verification,
            tool_calls=result.tool_calls,
            tool_failures=result.tool_failures,
            retention=retention,
            warnings=warnings,
            blocks=blocks,
            citations=report.citations,
            actions=actions,
        )

    detail = report.detail or (
        "The student is in scope, but no deterministic learning evidence is "
        "available yet."
    )
    errors.append(WorkspaceError(code="report_unavailable", detail=detail))
    blocks.append(
        ErrorStateBlock(
            id="workspace-report-unavailable",
            type="error_state",
            title="Learning evidence",
            priority="primary",
            payload=ErrorStatePayload(
                code="report_unavailable",
                headline="A grounded learning evidence report could not be assembled.",
                detail=detail,
                retryable=False,
            ),
        )
    )
    if actions:
        blocks.append(
            ActionListBlock(
                id="workspace-navigation-actions",
                type="action_list",
                title="Available screens",
                priority="secondary",
                payload=ActionListPayload(items=actions),
            )
        )
    return _base_response(
        request_id=request_id,
        correlation_id=correlation_id,
        message=WorkspaceMessage(
            title="Learning evidence unavailable",
            summary=detail,
            tone="blocked",
        ),
        verification=verification,
        tool_calls=result.tool_calls,
        tool_failures=result.tool_failures,
        retention=retention,
        errors=errors,
        blocks=blocks,
        citations=report.citations,
        actions=actions,
    )
