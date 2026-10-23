import assert from "node:assert/strict";
import test from "node:test";
import {
  KNOWN_KINDS,
  actionResultSucceeded,
  executeAction,
  fmt,
  isKnownKind,
  isSupportedActionEndpoint,
  mixedChildren,
  normalizeActionResponse,
  workflowIsRunning,
  workflowPhase,
  workflowStateLabel,
} from "../src/components/workspace/assistant-block-logic.ts";

const UUID = "d21fc36a-c574-4015-8096-b2ef8380e035";

test("all twelve result kinds are recognised", () => {
  assert.equal(KNOWN_KINDS.length, 12);
  for (const k of KNOWN_KINDS) assert.equal(isKnownKind(k), true);
});

test("unknown and missing kinds are not recognised (safe fallback path)", () => {
  assert.equal(isKnownKind("some_future_kind"), false);
  assert.equal(isKnownKind(undefined), false);
  assert.equal(isKnownKind(""), false);
});

// ── fmt ───────────────────────────────────────────────────────────────────────
test("fmt handles empty, money, percent, number, and raw", () => {
  assert.equal(fmt(null), "—");
  assert.equal(fmt(undefined), "—");
  assert.equal(fmt(""), "—");
  assert.equal(fmt(1200, "money"), "₹1,200");
  assert.equal(fmt(82.4, "percent"), "82%");
  assert.equal(fmt(41, "number"), "41");
  assert.equal(fmt("A1"), "A1");
  assert.equal(fmt("not-a-number", "number"), "not-a-number");
});

// ── action_result success gate (SAFETY) ─────────────────────────────────────────
test("confirmed action results show success", () => {
  assert.equal(actionResultSucceeded({ status: "completed", created: true }), true);
  assert.equal(actionResultSucceeded({ status: "published" }), true);
  // idempotent replay: created=false but completed is still a real success
  assert.equal(actionResultSucceeded({ status: "completed", created: false }), true);
});

test("unconfirmed / failed / expired action results NEVER show success", () => {
  assert.equal(actionResultSucceeded({ status: "failed" }), false);
  assert.equal(actionResultSucceeded({ status: "expired" }), false);
  assert.equal(actionResultSucceeded({ status: "rejected" }), false);
  assert.equal(actionResultSucceeded({}), false);
  assert.equal(actionResultSucceeded({ created: false }), false);
  // a bare created=false with no completed status must not imply success
  assert.equal(actionResultSucceeded({ created: false, status: "pending" }), false);
});

// ── workflow states ─────────────────────────────────────────────────────────────
test("workflowPhase maps every real backend state", () => {
  assert.equal(workflowPhase("created"), "pending");
  assert.equal(workflowPhase("queued"), "pending");
  assert.equal(workflowPhase("running"), "active");
  assert.equal(workflowPhase("waiting_for_input"), "attention");
  assert.equal(workflowPhase("waiting_for_approval"), "attention");
  assert.equal(workflowPhase("completed"), "done");
  assert.equal(workflowPhase("failed"), "failed");
  assert.equal(workflowPhase("cancelled"), "failed");
  assert.equal(workflowPhase("unknown_future"), "active"); // safe default
});

test("workflowIsRunning only for queued/running", () => {
  assert.equal(workflowIsRunning("queued"), true);
  assert.equal(workflowIsRunning("running"), true);
  assert.equal(workflowIsRunning("waiting_for_approval"), false);
  assert.equal(workflowIsRunning("completed"), false);
  assert.equal(workflowIsRunning(undefined), false);
});

test("workflowStateLabel humanises underscores, tolerates empty", () => {
  assert.equal(workflowStateLabel("waiting_for_approval"), "waiting for approval");
  assert.equal(workflowStateLabel("running"), "running");
  assert.equal(workflowStateLabel(undefined), "");
});

// ── mixed child ordering ─────────────────────────────────────────────────────────
test("mixedChildren is data-then-document, dropping nulls", () => {
  const data = { kind: "metrics" };
  const doc = { kind: "document" };
  assert.deepEqual(mixedChildren({ kind: "mixed", data, document: doc }), [data, doc]);
  assert.deepEqual(mixedChildren({ kind: "mixed", data, document: null }), [data]);
  assert.deepEqual(mixedChildren({ kind: "mixed", document: doc }), [doc]);
  assert.deepEqual(mixedChildren({ kind: "mixed" }), []);
});

// ── Action-endpoint allowlist (SAFETY: the UI is not a generic URL executor) ─────
test("supported governed action endpoints are accepted", () => {
  const uuid = "d21fc36a-c574-4015-8096-b2ef8380e035";
  assert.equal(
    isSupportedActionEndpoint("/api/v1/workflows/actions/publish-notice/confirm"),
    true
  );
  assert.equal(
    isSupportedActionEndpoint(`/api/v1/workflows/parent-intervention/drafts/${uuid}/approve`),
    true
  );
  assert.equal(isSupportedActionEndpoint(`/api/v1/ai/question-papers/${uuid}/submit`), true);
  assert.equal(isSupportedActionEndpoint(`/api/v1/ai/question-papers/${uuid}/approve`), true);
});

test("unsupported / unsafe endpoints are rejected (no request possible)", () => {
  const uuid = "d21fc36a-c574-4015-8096-b2ef8380e035";
  // external URL / scheme
  assert.equal(isSupportedActionEndpoint("https://evil.example.com/api/v1/x"), false);
  assert.equal(isSupportedActionEndpoint("//evil.example.com/api/v1/x"), false);
  // path traversal + query/fragment smuggling
  assert.equal(isSupportedActionEndpoint("/api/v1/../../etc/passwd"), false);
  assert.equal(
    isSupportedActionEndpoint("/api/v1/workflows/actions/publish-notice/confirm?x=1"),
    false
  );
  // off-allowlist internal paths (e.g. a destructive op not surfaced in chat)
  assert.equal(isSupportedActionEndpoint(`/api/v1/ai/question-papers/${uuid}/reject`), false);
  assert.equal(isSupportedActionEndpoint(`/api/v1/ai/question-papers/${uuid}`), false);
  assert.equal(isSupportedActionEndpoint("/api/v1/students/delete-all"), false);
  // malformed / empty / non-string
  assert.equal(isSupportedActionEndpoint(""), false);
  assert.equal(isSupportedActionEndpoint(undefined), false);
  assert.equal(isSupportedActionEndpoint(null), false);
  assert.equal(isSupportedActionEndpoint(42), false);
  // a non-uuid draft id must not match
  assert.equal(
    isSupportedActionEndpoint("/api/v1/workflows/parent-intervention/drafts/not-a-uuid/approve"),
    false
  );
});

// ── normalizeActionResponse: real backend contracts → action_result (success gate) ──
const NOTICE_EP = "/api/v1/workflows/actions/publish-notice/confirm";
const PARENT_EP = `/api/v1/workflows/parent-intervention/drafts/${UUID}/approve`;
const QP_SUBMIT_EP = `/api/v1/ai/question-papers/${UUID}/submit`;
const QP_APPROVE_EP = `/api/v1/ai/question-papers/${UUID}/approve`;

test("notice publish: created=true in the real APIResponse envelope → success", () => {
  const raw = {
    data: {
      kind: "action_result",
      action: "publish_notice",
      status: "completed",
      notice_id: "n-1",
      audience: "external",
      created: true,
    },
    message: "Notice published",
  };
  const block = normalizeActionResponse(NOTICE_EP, raw);
  assert.equal(block.kind, "action_result");
  assert.equal(block.created, true);
  assert.equal(block.notice_id, "n-1");
  assert.equal(actionResultSucceeded(block), true);
});

test("notice publish: idempotent replay created=false status=completed → still success", () => {
  const raw = { data: { status: "completed", created: false, notice_id: "n-1" } };
  const block = normalizeActionResponse(NOTICE_EP, raw);
  assert.equal(actionResultSucceeded(block), true); // completed replay is a real success
});

test("parent intervention: notification_id present → notified (success)", () => {
  const block = normalizeActionResponse(PARENT_EP, {
    data: { draft_id: UUID, status: "approved", notification_id: "notif-9" },
  });
  assert.equal(block.created, true);
  assert.equal(actionResultSucceeded(block), true);
});

test("parent intervention: missing/null notification_id → NOT notified (not success)", () => {
  const missing = normalizeActionResponse(PARENT_EP, { data: { draft_id: UUID, status: "approved" } });
  assert.equal(missing.created, false);
  assert.equal(actionResultSucceeded(missing), false);
  const nulled = normalizeActionResponse(PARENT_EP, {
    data: { draft_id: UUID, notification_id: null },
  });
  assert.equal(actionResultSucceeded(nulled), false);
});

test("QP submit: pending_approval → success", () => {
  const block = normalizeActionResponse(QP_SUBMIT_EP, { id: UUID, status: "pending_approval" });
  assert.equal(block.action, "submit_question_paper");
  assert.equal(actionResultSucceeded(block), true);
});

test("QP approve: approved → success", () => {
  const block = normalizeActionResponse(QP_APPROVE_EP, { id: UUID, status: "approved" });
  assert.equal(block.action, "approve_question_paper");
  assert.equal(actionResultSucceeded(block), true);
});

test("unexpected / malformed responses are NEVER silently marked success", () => {
  // An unexpected QP status (e.g. still draft) is not a success.
  assert.equal(actionResultSucceeded(normalizeActionResponse(QP_APPROVE_EP, { status: "draft" })), false);
  // Malformed bodies for each endpoint → not success.
  assert.equal(actionResultSucceeded(normalizeActionResponse(NOTICE_EP, {})), false);
  assert.equal(actionResultSucceeded(normalizeActionResponse(NOTICE_EP, null)), false);
  assert.equal(actionResultSucceeded(normalizeActionResponse(PARENT_EP, {})), false);
  assert.equal(actionResultSucceeded(normalizeActionResponse(QP_SUBMIT_EP, {})), false);
  assert.equal(actionResultSucceeded(normalizeActionResponse(QP_SUBMIT_EP, "not-json")), false);
});

// ── executeAction: validate-before-send + transport usage ────────────────────────
test("executeAction rejects an unsupported endpoint WITHOUT calling the transport", async () => {
  let called = false;
  const transport = async () => {
    called = true;
    return {};
  };
  await assert.rejects(
    () => executeAction("/api/v1/students/delete-all", {}, transport),
    /isn't supported/
  );
  await assert.rejects(
    () => executeAction("https://evil.example.com/x", {}, transport),
    /isn't supported/
  );
  assert.equal(called, false); // no request was ever attempted
});

test("executeAction calls the transport for a supported endpoint and normalizes the result", async () => {
  const calls = [];
  const transport = async (endpoint, body) => {
    calls.push({ endpoint, body });
    return { data: { status: "completed", created: true, notice_id: "n-1" } };
  };
  const payload = { action_token: "tok", title: "Holiday" };
  const block = await executeAction(NOTICE_EP, payload, transport);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].endpoint, NOTICE_EP);
  assert.deepEqual(calls[0].body, payload); // the contractual payload is forwarded verbatim
  assert.equal(actionResultSucceeded(block), true);
});

test("executeAction propagates a transport (server) failure as a throw, never success", async () => {
  const transport = async () => {
    throw new Error("Unauthorized");
  };
  await assert.rejects(() => executeAction(QP_APPROVE_EP, {}, transport), /Unauthorized/);
});
