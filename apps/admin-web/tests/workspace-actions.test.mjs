import assert from "node:assert/strict";
import test from "node:test";
import {
  WORKSPACE_ACTIONS,
  WORKSPACE_HERO,
  WORKSPACE_PROMPTS,
  heroForRole,
  promptsForRole,
  roleToWorkspaceRole,
} from "../src/lib/workspace-actions.ts";

const ROLES = ["admin", "teacher", "parent", "student"];

test("role mapping collapses backend roles to the four workspace personas", () => {
  assert.equal(roleToWorkspaceRole("super_admin"), "admin");
  assert.equal(roleToWorkspaceRole("admin"), "admin");
  assert.equal(roleToWorkspaceRole("operations"), "admin");
  assert.equal(roleToWorkspaceRole("teacher"), "teacher");
  assert.equal(roleToWorkspaceRole("class_incharge"), "teacher");
  assert.equal(roleToWorkspaceRole("parent"), "parent");
  assert.equal(roleToWorkspaceRole("student"), "student");
});

test("unknown / undefined roles fall back to admin (never crash, never a wider persona)", () => {
  assert.equal(roleToWorkspaceRole(undefined), "admin");
  assert.equal(roleToWorkspaceRole(""), "admin");
  assert.equal(roleToWorkspaceRole("martian"), "admin");
  assert.deepEqual(heroForRole("martian"), WORKSPACE_HERO.admin);
  assert.deepEqual(promptsForRole(undefined), WORKSPACE_PROMPTS.admin);
});

test("every persona has a non-empty hero and at least three prompts", () => {
  for (const r of ROLES) {
    const hero = heroForRole(r);
    assert.ok(hero.title.length > 0, `${r} hero title`);
    assert.ok(hero.subtitle.length > 0, `${r} hero subtitle`);
    assert.ok(promptsForRole(r).length >= 3, `${r} prompts`);
  }
});

test("parent prompts surface the real parent conversational capabilities", () => {
  const joined = promptsForRole("parent").join(" | ").toLowerCase();
  assert.match(joined, /child/);       // progress
  assert.match(joined, /attendance/);  // attendance
  assert.match(joined, /improve|weak|subject/); // weak topics
  assert.match(joined, /fee/);         // fees
});

test("student prompts surface the real student conversational capabilities", () => {
  const joined = promptsForRole("student").join(" | ").toLowerCase();
  assert.match(joined, /study|learn/);     // daily plan
  assert.match(joined, /weak|topic/);      // weak topics
  assert.match(joined, /explain|tutor/);   // tutoring
});

test("admin and teacher prompts reflect their own supported capabilities", () => {
  const admin = promptsForRole("admin").join(" | ").toLowerCase();
  assert.match(admin, /school|fee|attendance|students/);
  const teacher = promptsForRole("teacher").join(" | ").toLowerCase();
  assert.match(teacher, /learning evidence|attendance|assessment/);
});

test("no cross-role prompt leakage: parent/student never see staff-only prompts", () => {
  const parent = promptsForRole("parent").join(" | ").toLowerCase();
  const student = promptsForRole("student").join(" | ").toLowerCase();
  for (const forbidden of ["learning evidence", "fee collection", "open staff", "finance"]) {
    assert.ok(!parent.includes(forbidden), `parent leaked: ${forbidden}`);
    assert.ok(!student.includes(forbidden), `student leaked: ${forbidden}`);
  }
  // Students must not be shown fee/finance prompts (not their capability).
  assert.ok(!student.includes("fee"), "student leaked fees");
});

test("no cross-role action leakage: each persona's action grid is its own", () => {
  // Parent/student action grids must not contain staff-only action ids.
  const parentIds = WORKSPACE_ACTIONS.parent.map((a) => a.id);
  const studentIds = WORKSPACE_ACTIONS.student.map((a) => a.id);
  for (const staffOnly of ["staff", "finance", "learning-evidence", "school-overview"]) {
    assert.ok(!parentIds.includes(staffOnly), `parent action leaked: ${staffOnly}`);
    assert.ok(!studentIds.includes(staffOnly), `student action leaked: ${staffOnly}`);
  }
});

test("prompts/actions are presentation only — they carry no permission or authority flags", () => {
  // A prompt is a plain string; an action is a display def with an intent string, never a
  // grant. Authorization is server-side; nothing here encodes access.
  for (const r of ROLES) {
    for (const p of promptsForRole(r)) assert.equal(typeof p, "string");
    for (const a of WORKSPACE_ACTIONS[r]) {
      assert.equal(typeof a.intent, "string");
      assert.ok(!("permission" in a) && !("allow" in a) && !("grant" in a));
    }
  }
});
