/** Client for the agentic workspace assistant (plan -> governed tool -> blocks). */
import { api } from "@/lib/api";

export interface AssistantMetric {
  label: string;
  value: string | number | null;
  format?: "number" | "money" | "percent";
}

export interface AssistantColumn {
  key: string;
  label: string;
  format?: "number" | "money" | "percent";
}

export interface AssistantNavSuggestion {
  label: string;
  href: string;
}

export interface AssistantClarifyOption {
  id: string;
  label: string;
}

export interface AssistantCitation {
  title: string;
  document_type?: string | null;
  snippet?: string | null;
}

/** An action/link the assistant surfaces on a workflow block. */
export interface AssistantAction {
  label: string;
  href?: string;
}

/** The confirm step on an action_preview block (human-in-the-loop gate). */
export interface AssistantConfirmAction {
  label: string;
  endpoint: string;
  payload?: Record<string, unknown>;
}

/**
 * A typed result block the assistant returns; render varies by `kind`.
 *
 * `kind` mirrors the backend contract in app/modules/workspace/assistant/result.py.
 * The trailing `string` keeps forward-compatibility: an unknown future kind is tolerated,
 * not type-errored.
 */
export interface AssistantBlock {
  kind:
    | "metrics"
    | "table"
    | "navigate"
    | "guide"
    | "error"
    | "clarify"
    | "not_found"
    | "document"
    | "mixed"
    | "workflow"
    | "action_preview"
    | "action_result"
    | string;
  title?: string;
  subtitle?: string;
  source?: string;
  metrics?: AssistantMetric[];
  columns?: AssistantColumn[];
  rows?: Array<Record<string, unknown>>;
  empty_message?: string;
  href?: string;
  href_label?: string;
  label?: string;
  message?: string;
  suggestions?: AssistantNavSuggestion[];
  options?: AssistantClarifyOption[];
  citations?: AssistantCitation[];
  data?: AssistantBlock;
  document?: AssistantBlock | null;
  // workflow
  workflow_id?: string;
  workflow_state?: string;
  summary?: Record<string, unknown>;
  actions?: AssistantAction[];
  // action_preview
  action?: string;
  status?: string;
  preview?: Record<string, unknown>;
  confirm_action?: AssistantConfirmAction;
  // action_result (returned by the confirm endpoint; may also render in history)
  notice_id?: string;
  audience?: string;
  created?: boolean;
}

export interface AssistantTurn {
  session_id: string;
  result_kind: string;
  block: AssistantBlock;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  updated_at: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  result_kind?: string | null;
  payload?: AssistantBlock | null;
}

export async function assistantTurn(text: string, sessionId?: string | null): Promise<AssistantTurn> {
  const res = await api<{ data: AssistantTurn }>("/api/v1/workspace/assistant/turn", {
    method: "POST",
    body: JSON.stringify({ text, session_id: sessionId ?? null }),
  });
  return res.data;
}

export async function listChatSessions(): Promise<ChatSessionSummary[]> {
  const res = await api<{ data: ChatSessionSummary[] }>("/api/v1/workspace/assistant/sessions");
  return res.data ?? [];
}

export async function getChatSession(sessionId: string): Promise<ChatMessage[]> {
  const res = await api<{ data: ChatMessage[] }>(
    `/api/v1/workspace/assistant/sessions/${sessionId}`
  );
  return res.data ?? [];
}

/** A background job's pollable status (e.g. async question-paper generation). */
export interface JobStatusOut {
  id: string;
  type: string;
  status: "queued" | "running" | "done" | "failed";
  result?: Record<string, unknown> | null;
  error?: string | null;
}

/** Poll one job the current user owns. Tenant- and creator-scoped server-side (404 otherwise). */
export async function getJob(jobId: string): Promise<JobStatusOut> {
  const res = await api<{ data: JobStatusOut }>(`/api/v1/jobs/${jobId}`);
  return res.data;
}
