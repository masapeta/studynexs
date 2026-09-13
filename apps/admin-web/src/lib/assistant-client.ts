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

/** A typed result block the assistant returns; render varies by `kind`. */
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
