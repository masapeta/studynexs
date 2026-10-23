/**
 * Pure, render-independent decision logic for the assistant block renderer.
 *
 * Extracted from AssistantBlockView so the safety-critical rules — especially "never imply an
 * action succeeded unless the backend confirmed it" — are unit-testable without a DOM. These are
 * the only places a rendering decision could silently go wrong; keep them here, not inline in JSX.
 */

import type { AssistantBlock } from "@/lib/assistant-client";

/** The twelve known result kinds. An unknown kind is tolerated (safe fallback), never crashed. */
export const KNOWN_KINDS = [
  "metrics",
  "table",
  "guide",
  "error",
  "clarify",
  "not_found",
  "document",
  "mixed",
  "navigate",
  "workflow",
  "action_preview",
  "action_result",
] as const;

export function isKnownKind(kind: string | undefined): boolean {
  return typeof kind === "string" && (KNOWN_KINDS as readonly string[]).includes(kind);
}

/** Format a metric/table value for display. Mirrors the renderer's `fmt`. */
export function fmt(value: unknown, format?: "number" | "money" | "percent"): string {
  if (value === null || value === undefined || value === "") return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  if (format === "money") return `₹${num.toLocaleString("en-IN")}`;
  if (format === "percent") return `${Math.round(num)}%`;
  if (format === "number") return num.toLocaleString("en-IN");
  return String(value);
}

/**
 * Whether an `action_result` block may be shown as a success.
 *
 * SAFETY: a displayed action result must never imply success unless the backend confirmed it.
 * The confirm endpoint returns `status: "completed"` with `created` (true = newly done, false =
 * idempotent replay of an already-done action — still a real success), or `status: "published"`.
 * Anything else (failed, expired, rejected, missing) is NOT a success.
 */
export function actionResultSucceeded(block: Pick<AssistantBlock, "created" | "status">): boolean {
  if (block.created === true) return true;
  if (block.created === false && block.status === "completed") return true;
  return block.status === "published";
}

/** Lifecycle states the backend workflow contract (WorkflowState) actually emits. */
export const WORKFLOW_STATES = [
  "created",
  "queued",
  "running",
  "waiting_for_input",
  "waiting_for_approval",
  "completed",
  "failed",
  "cancelled",
] as const;

export type WorkflowPhase = "pending" | "active" | "attention" | "done" | "failed";

/** Coarse phase for choosing an icon/tone, derived from the authoritative workflow_state. */
export function workflowPhase(state: string | undefined): WorkflowPhase {
  switch (state) {
    case "queued":
    case "created":
      return "pending";
    case "running":
      return "active";
    case "waiting_for_input":
    case "waiting_for_approval":
      return "attention";
    case "completed":
      return "done";
    case "failed":
    case "cancelled":
      return "failed";
    default:
      return "active";
  }
}

/** A workflow is still progressing (poll its job) when queued or running. */
export function workflowIsRunning(state: string | undefined): boolean {
  return state === "queued" || state === "running";
}

/** Human label for a workflow_state (underscores → spaces), safe for an unknown value. */
export function workflowStateLabel(state: string | undefined): string {
  if (!state) return "";
  return state.replace(/_/g, " ");
}

/**
 * The ordered child blocks of a `mixed` result. Stable order: data first, then document.
 * Nulls/absent children are dropped so the renderer never emits an empty slot.
 */
export function mixedChildren(block: AssistantBlock): AssistantBlock[] {
  const out: AssistantBlock[] = [];
  if (block.data) out.push(block.data);
  if (block.document) out.push(block.document);
  return out;
}

/**
 * The EXACT internal POST operations the chat UI may invoke from a server-issued action/workflow
 * endpoint. This is a frontend allowlist (defense-in-depth) — the server still re-authorizes,
 * re-validates, enforces tenancy/idempotency, and audits every call. The UI is NOT a generic URL
 * executor: anything not matching one of these patterns produces NO request.
 */
export const SUPPORTED_ACTION_ENDPOINTS: readonly RegExp[] = [
  /^\/api\/v1\/workflows\/actions\/publish-notice\/confirm$/,
  /^\/api\/v1\/workflows\/parent-intervention\/drafts\/[0-9a-fA-F-]{36}\/approve$/,
  /^\/api\/v1\/ai\/question-papers\/[0-9a-fA-F-]{36}\/(submit|approve)$/,
];

/**
 * Whether an endpoint string is a supported internal action the UI may POST to. Rejects external
 * URLs, schemes, path traversal, query/fragment smuggling, and anything off the allowlist.
 */
export function isSupportedActionEndpoint(endpoint: unknown): endpoint is string {
  if (typeof endpoint !== "string" || endpoint.length === 0) return false;
  // Internal, absolute API paths only — never a scheme/host, never traversal or query tricks.
  if (!endpoint.startsWith("/api/v1/")) return false;
  if (endpoint.includes("://") || endpoint.includes("..") || /[?#]/.test(endpoint)) return false;
  return SUPPORTED_ACTION_ENDPOINTS.some((re) => re.test(endpoint));
}

/**
 * Turn a confirmed backend action/workflow response into the `action_result` block the chat
 * renders. Different governed endpoints return different shapes — we translate each to the common
 * contract WITHOUT ever inventing success: the block's fields come straight from the server, and
 * the renderer's success gate (`actionResultSucceeded`) decides what's shown as done. Pure (no
 * I/O) so it is unit-testable against the real production response contracts.
 */
export function normalizeActionResponse(endpoint: string, raw: unknown): AssistantBlock {
  const body = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  // Publish-notice already returns a fully-formed action_result inside the APIResponse envelope.
  if (endpoint.endsWith("/publish-notice/confirm")) {
    const data = (body.data && typeof body.data === "object" ? body.data : {}) as Record<
      string,
      unknown
    >;
    return {
      kind: "action_result",
      action: typeof data.action === "string" ? data.action : "publish_notice",
      status: typeof data.status === "string" ? data.status : undefined,
      created: data.created === true,
      notice_id: typeof data.notice_id === "string" ? data.notice_id : undefined,
      audience: typeof data.audience === "string" ? data.audience : undefined,
      title: data.created ? "Notice published" : "Notice already published",
      message: data.created
        ? "The notice has been published."
        : "This notice was already published.",
    };
  }
  // Parent intervention approve → notified only when a notification id came back.
  if (endpoint.includes("/parent-intervention/drafts/")) {
    const data = (body.data && typeof body.data === "object" ? body.data : {}) as Record<
      string,
      unknown
    >;
    const notified = Boolean(data.notification_id);
    return {
      kind: "action_result",
      action: "approve_and_notify",
      status: notified ? "completed" : "not_sent",
      created: notified,
      title: notified ? "Parent notified" : "Not sent",
      message: notified
        ? "The parent has been notified."
        : "The approval did not produce a notification.",
    };
  }
  // Question Paper submit/approve return a flat QuestionPaperOut (no envelope); map its status.
  if (endpoint.includes("/question-papers/")) {
    const status = typeof body.status === "string" ? body.status : "";
    const approved = status === "approved";
    const submitted = status === "pending_approval";
    const ok = approved || submitted;
    return {
      kind: "action_result",
      action: endpoint.endsWith("/approve") ? "approve_question_paper" : "submit_question_paper",
      status: ok ? "completed" : status || undefined,
      created: ok,
      title: approved
        ? "Question paper approved"
        : submitted
          ? "Submitted for approval"
          : "Action complete",
      message: approved
        ? "The question paper is approved."
        : submitted
          ? "The question paper was submitted for approval."
          : "The request was processed.",
    };
  }
  // Unknown (should be unreachable — the caller validates against the allowlist first).
  return {
    kind: "action_result",
    status: undefined,
    created: false,
    title: "Action complete",
    message: "The request was processed.",
  };
}

/** A minimal POST transport: returns the parsed JSON body, throws on failure (e.g. the api() client). */
export type ActionTransport = (
  endpoint: string,
  payload: Record<string, unknown>
) => Promise<unknown>;

/**
 * Execute a governed action through an injected transport. Validates the endpoint against the
 * allowlist BEFORE any transport call (an unsupported endpoint throws and sends nothing), then
 * normalizes the confirmed response. Transport is injected so this orchestration is unit-testable
 * without the network; production binds the authenticated `api()` client.
 */
export async function executeAction(
  endpoint: string,
  payload: Record<string, unknown> | undefined,
  transport: ActionTransport
): Promise<AssistantBlock> {
  if (!isSupportedActionEndpoint(endpoint)) {
    throw new Error("This action isn't supported.");
  }
  const raw = await transport(endpoint, payload ?? {});
  return normalizeActionResponse(endpoint, raw);
}
