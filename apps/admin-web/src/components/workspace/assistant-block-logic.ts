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
