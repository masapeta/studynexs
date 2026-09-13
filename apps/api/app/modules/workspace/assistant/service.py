"""Agentic assistant service: plan -> run governed tool -> typed blocks, with history.

Flow: persist the user turn, ask the planner to choose a governed tool + params
(grounded, metered LLM), execute the deterministic tenant-scoped service, persist
and return the assistant turn. Session history gives follow-up context.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.models.workspace_chat import WorkspaceChatMessage, WorkspaceChatSession
from app.modules.workspace.assistant.planner import NAV_TARGETS, plan
from app.modules.workspace.assistant.tools import get_tool, tools_for_role

logger = structlog.get_logger()

_MAX_HISTORY_TURNS = 8


class AssistantService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _get_or_create_session(
        self, *, school_id: uuid.UUID, user_id: uuid.UUID, session_id: uuid.UUID | None, title: str
    ) -> WorkspaceChatSession:
        if session_id is not None:
            existing = await self.db.scalar(
                select(WorkspaceChatSession).where(
                    WorkspaceChatSession.id == session_id,
                    WorkspaceChatSession.school_id == school_id,
                    WorkspaceChatSession.user_id == user_id,
                )
            )
            if existing is not None:
                return existing
        session = WorkspaceChatSession(
            school_id=school_id, user_id=user_id, title=title[:200] or "New chat"
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def _resolve_range(self, school_id: uuid.UUID, time: Any):
        """Resolve a planner temporal token into a concrete DateRange (tenant timezone)."""
        from app.db.models.school import School
        from app.modules.workspace.assistant.temporal import resolve_time_range

        school = await self.db.get(School, school_id)
        return await resolve_time_range(self.db, school, school_id, time)

    async def _history(self, session_id: uuid.UUID) -> list[dict[str, str]]:
        rows = (
            await self.db.execute(
                select(WorkspaceChatMessage.role, WorkspaceChatMessage.text)
                .where(WorkspaceChatMessage.session_id == session_id)
                .order_by(WorkspaceChatMessage.created_at.desc())
                .limit(_MAX_HISTORY_TURNS)
            )
        ).all()
        # Oldest first for the model.
        return [{"role": r, "text": t} for r, t in reversed(rows)]

    async def handle_turn(
        self,
        *,
        current_user: CurrentUser,
        text: str,
        session_id: uuid.UUID | None,
    ) -> dict[str, Any]:
        school_id = uuid.UUID(current_user.school_id)
        user_id = uuid.UUID(current_user.id)
        role = current_user.role

        session = await self._get_or_create_session(
            school_id=school_id, user_id=user_id, session_id=session_id, title=text
        )

        # Persist the user turn.
        self.db.add(
            WorkspaceChatMessage(
                school_id=school_id, session_id=session.id, role="user", text=text
            )
        )
        await self.db.flush()

        history = await self._history(session.id)
        tools = tools_for_role(role)
        decision = await plan(text, tools=tools, history=history[:-1])

        block: dict[str, Any]
        # Non-sensitive execution trace for observability + eval (spec §24, §25).
        trace: dict[str, Any] = {
            "route": decision.route,
            "action": decision.action,
            "capability": decision.tool,
            "params": {k: v for k, v in (decision.params or {}).items() if k != "_range"},
            "document_query": decision.document_query,
            "time_range": None,
        }

        if decision.action == "tool":
            block = await self._run_tool(
                current_user, decision.tool, decision.params, school_id, trace=trace
            )
        elif decision.action == "compose":
            block = await self._run_compose(current_user, decision.plan, school_id, trace=trace)
        elif decision.action == "mixed":
            block = await self._run_mixed(current_user, decision, school_id, trace=trace)
        elif decision.action == "document":
            block = await self._run_document(
                school_id, decision.document_query or decision.message or text
            )
        elif decision.action == "act":
            block = self._action_not_supported(decision)
        elif decision.action == "navigate" and decision.navigate_to in NAV_TARGETS:
            block = {
                "kind": "navigate",
                "title": "Opening",
                "href": NAV_TARGETS[decision.navigate_to],
                "label": decision.navigate_to.replace("-", " ").title(),
            }
        else:
            block = self._guide_block(role, message=decision.message)
        result_kind = block.get("kind", "data")
        trace["result_kind"] = result_kind

        # Persist the assistant turn (payload = the block for redisplay in history).
        self.db.add(
            WorkspaceChatMessage(
                school_id=school_id,
                session_id=session.id,
                role="assistant",
                text=block.get("title", ""),
                result_kind=result_kind,
                payload=block,
            )
        )
        await self.db.flush()

        return {
            "session_id": str(session.id),
            "result_kind": result_kind,
            "block": block,
            "trace": trace,
        }

    async def _run_tool(
        self,
        current_user: CurrentUser,
        tool_name: str | None,
        raw_params: dict[str, Any] | None,
        school_id: uuid.UUID,
        *,
        trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute one governed structured tool with temporal resolution + error safety."""
        tool = get_tool(tool_name) if tool_name else None
        if tool is None or not tool.allowed_for(current_user.role):
            return self._guide_block(current_user.role)
        params = dict(raw_params or {})
        if "time" in params:
            rng = await self._resolve_range(school_id, params.get("time"))
            params["_range"] = rng
            if trace is not None:
                trace["time_range"] = {
                    "label": rng.label,
                    "temporality": rng.temporality,
                    "start": rng.start.isoformat() if rng.start else None,
                    "end": rng.end.isoformat() if rng.end else None,
                    "start_date": rng.start_date.isoformat() if rng.start_date else None,
                    "end_date": rng.end_date.isoformat() if rng.end_date else None,
                }
            # Historical-honesty guard (P0): a current-state relationship capability cannot
            # answer a PAST request — the ERP has no effective-dated history. Block BEFORE
            # executing the current-state query; never silently substitute present data.
            if rng.is_past and not tool.supports_historical:
                if trace is not None:
                    trace["historical_guard"] = {
                        "historical": True,
                        "capability": tool.name,
                        "supports_historical": tool.supports_historical,
                        "decision": "blocked",
                    }
                logger.info(
                    "assistant_historical_blocked", tool=tool.name, period=rng.label
                )
                return self._historical_unavailable_block(tool.name, rng.label)
        try:
            return await tool.handler(self.db, current_user, params)
        except Exception as exc:  # noqa: BLE001 — never crash the turn
            logger.warning("assistant_tool_failed", tool=tool.name, error=str(exc))
            return {
                "kind": "error",
                "title": "Couldn't complete that",
                "message": "That request could not be completed right now.",
            }

    async def _run_compose(
        self,
        current_user: CurrentUser,
        raw_plan: dict[str, Any] | None,
        school_id: uuid.UUID,
        *,
        trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """COMPOSE route: validate + execute a bounded multi-capability plan (Phase 4)."""
        from app.modules.workspace.assistant.composition import (
            CompositionError,
            execute_plan,
            parse_plan,
        )

        if not raw_plan:
            return self._guide_block(current_user.role)
        # Composition spans classes/students school-wide; restrict to admin/principal so a
        # scoped teacher can't see beyond their classes via a composed plan (spec §20).
        if current_user.role not in ("admin", "super_admin"):
            return self._guide_block(current_user.role)
        try:
            plan = parse_plan(raw_plan)
        except CompositionError as exc:
            logger.warning("assistant_compose_invalid_plan", error=str(exc))
            return self._guide_block(current_user.role)
        try:
            result = await execute_plan(
                self.db, current_user, plan, resolve_range=self._resolve_range
            )
        except CompositionError as exc:
            # e.g. class not found mid-plan — honest, not fabricated.
            return {
                "kind": "not_found",
                "title": "Couldn't complete that",
                "message": str(exc),
            }
        except Exception as exc:  # noqa: BLE001 — never crash the turn
            logger.warning("assistant_compose_failed", error=str(exc))
            return {
                "kind": "error",
                "title": "Couldn't complete that",
                "message": "That request could not be completed right now.",
            }

        if trace is not None:
            trace["operations"] = result.trace_ops

        pretty = {
            "class_label": "Class", "student_count": "Students", "attendance_pct": "Attendance %",
            "class_teacher": "Class Teacher", "subject_teachers": "Teachers", "name": "Student",
            "admission_no": "Admission no", "fee_due": "Fee due",
        }
        col_fmt = {"attendance_pct": "percent", "fee_due": "money"}
        columns = [
            {"key": c, "label": pretty.get(c, c.replace("_", " ").title()), **(
                {"format": col_fmt[c]} if c in col_fmt else {}
            )}
            for c in result.columns
        ]
        return {
            "kind": "table",
            "title": "Result",
            "source": "Composed query (live ERP)",
            "columns": columns,
            "rows": result.rows,
            "empty_message": "No records match all the conditions.",
        }

    async def _run_document(self, school_id: uuid.UUID, query: str) -> dict[str, Any]:
        """DOCUMENT route: retrieve school-policy knowledge (honest when unconfigured)."""
        from app.modules.workspace.assistant.documents import get_document_provider

        answer = await get_document_provider().search(school_id=school_id, query=query)
        if not answer.configured:
            return {
                "kind": "guide",
                "title": "Policy knowledge isn't set up yet",
                "message": (
                    "I can answer live questions about students, attendance, fees and staff. "
                    "A school policy/handbook knowledge base hasn't been configured for this "
                    "school yet, so I can't quote policy. Once policies are uploaded, I'll "
                    "answer these directly."
                ),
                "suggestions": [{"label": "Open notices", "href": "/dashboard/notices"}],
            }
        if not answer.has_matches:
            return {
                "kind": "not_found",
                "title": "No matching policy found",
                "message": f"I couldn't find a policy answering “{query}”.",
            }
        return {
            "kind": "document",
            "title": "From school policy",
            "message": answer.context_text,
            "citations": [
                {"title": c.title, "document_type": c.document_type, "snippet": c.snippet}
                for c in answer.citations
            ],
        }

    async def _run_mixed(
        self,
        current_user: CurrentUser,
        decision: Any,
        school_id: uuid.UUID,
        *,
        trace: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """MIXED route: run the structured data step, then the policy step, then combine."""
        data_block = await self._run_tool(
            current_user, decision.tool, decision.params, school_id, trace=trace
        )
        doc_query = decision.document_query or decision.message or ""
        doc_block = await self._run_document(school_id, doc_query) if doc_query else None
        return {
            "kind": "mixed",
            "title": data_block.get("title", "Result"),
            "data": data_block,
            "document": doc_block,
        }

    # Capability -> what current state it reflects, for the honesty message.
    _HISTORICAL_SUBJECT = {
        "teachers_for_class": "teacher assignments",
        "teacher_assignments": "teacher assignments",
        "class_roster": "class enrolment",
        "student_profile": "class enrolment",
    }

    def _historical_unavailable_block(self, capability: str, period: str) -> dict[str, Any]:
        """Honest response when a PAST request hits a current-state capability (P0)."""
        subject = self._HISTORICAL_SUBJECT.get(capability, "this relationship")
        return {
            "kind": "not_found",
            "title": "Historical records not available",
            "message": (
                f"I can show the current {subject}, but StudyNexs doesn't keep historical "
                f"{subject} records, so I can't reliably tell you how it was for {period}."
            ),
        }

    def _action_not_supported(self, decision: Any) -> dict[str, Any]:
        """ACTION route recognized but writes require explicit confirmation (spec §21)."""
        return {
            "kind": "guide",
            "title": "This would change data",
            "message": (
                "I understood that as a request to change data. For safety, actions that "
                "modify records aren't executed from chat yet. Please use the relevant "
                "screen to make this change."
            ),
            "suggestions": [
                {"label": "Attendance", "href": "/dashboard/attendance"},
                {"label": "Finance", "href": "/dashboard/finance"},
                {"label": "Students", "href": "/dashboard/students"},
            ],
        }

    def _guide_block(self, role: str, *, message: str | None = None) -> dict[str, Any]:
        is_staff = role in {"admin", "super_admin", "class_incharge", "teacher", "operations"}
        suggestions = (
            [
                {"label": "Students", "href": "/dashboard/students"},
                {"label": "Attendance", "href": "/dashboard/attendance"},
                {"label": "Finance", "href": "/dashboard/finance"},
                {"label": "Assessments", "href": "/dashboard/teaching"},
                {"label": "Classes", "href": "/dashboard/classes"},
                {"label": "Notices", "href": "/dashboard/notices"},
            ]
            if is_staff
            else [
                {"label": "Home", "href": "/parent"},
                {"label": "Notices", "href": "/parent/notices"},
            ]
        )
        return {
            "kind": "guide",
            "title": "I can take you to the right place",
            "message": message
            or "I don't have a verified answer for that yet. Here's where that usually lives.",
            "suggestions": suggestions,
        }

    async def list_sessions(
        self, *, current_user: CurrentUser, limit: int = 30
    ) -> list[dict[str, Any]]:
        rows = (
            await self.db.execute(
                select(WorkspaceChatSession)
                .where(
                    WorkspaceChatSession.school_id == uuid.UUID(current_user.school_id),
                    WorkspaceChatSession.user_id == uuid.UUID(current_user.id),
                )
                .order_by(WorkspaceChatSession.updated_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return [
            {
                "id": str(s.id),
                "title": s.title,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in rows
        ]

    async def get_session_messages(
        self, *, current_user: CurrentUser, session_id: uuid.UUID
    ) -> list[dict[str, Any]]:
        session = await self.db.scalar(
            select(WorkspaceChatSession).where(
                WorkspaceChatSession.id == session_id,
                WorkspaceChatSession.school_id == uuid.UUID(current_user.school_id),
                WorkspaceChatSession.user_id == uuid.UUID(current_user.id),
            )
        )
        if session is None:
            return []
        rows = (
            await self.db.execute(
                select(WorkspaceChatMessage)
                .where(WorkspaceChatMessage.session_id == session_id)
                .order_by(WorkspaceChatMessage.created_at)
            )
        ).scalars().all()
        return [
            {
                "role": m.role,
                "text": m.text,
                "result_kind": m.result_kind,
                "payload": m.payload,
            }
            for m in rows
        ]
