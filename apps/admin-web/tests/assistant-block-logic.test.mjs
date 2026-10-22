import assert from "node:assert/strict";
import test from "node:test";
import {
  KNOWN_KINDS,
  actionResultSucceeded,
  fmt,
  isKnownKind,
  mixedChildren,
  workflowIsRunning,
  workflowPhase,
  workflowStateLabel,
} from "../src/components/workspace/assistant-block-logic.ts";

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
