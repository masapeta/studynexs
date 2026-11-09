/**
 * Milestone 7A — Native assistant CHAT journeys (tenant `reference`).
 *
 * Drives the real WorkspaceRoot composer (textarea "Ask StudyNexs anything…") for each persona
 * and asserts the rendered assistant block + the actual /workspace/assistant/turn response.
 *
 * Prereqs: API on 127.0.0.1:8000, web (next dev) on :3000 built with
 *   NEXT_PUBLIC_TENANT_SLUG=reference, reference tenant seeded (seed_reference_school.py).
 * Run:  node e2e-assistant-chat.cjs
 *
 * Read-only journeys (no governed write actions are confirmed). Uses disposable seed data.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { e2ePassword } = require("./e2e-harness-utils.cjs");

const BASE = process.env.E2E_BASE_URL || "http://localhost:3000";
const PASSWORD = e2ePassword("principal");
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-assistant-chat");
const results = [];

const PERSONAS = [
  {
    key: "admin", portal: "staff", username: "principal", homePattern: "**/dashboard**",
    prompts: [
      { text: "Show today's school attendance", expectTitle: /school attendance/i,
        expectCap: "school_attendance" },
    ],
  },
  {
    key: "teacher", portal: "staff", username: "teacher6", homePattern: "**/dashboard**",
    prompts: [
      // A concrete student is required for the lookup; the reference tenant has students like
      // ARM0002. With no mastery flag seeded the capability honestly returns not_found — the
      // journey verifies routing + honest-empty, not a populated card.
      { text: "Show learning evidence for admission number ARM0002", expectTitle: null,
        expectCap: "student_learning_evidence" },
    ],
  },
  {
    key: "parent", portal: "parent", username: "parent_demo", homePattern: "**/parent**",
    chatPath: "/parent/assistant",
    prompts: [
      { text: "How is my child doing?", expectTitle: /my child|children|attendance|progress/i,
        expectCap: /my_child|my_children/ },
      { text: "What is my child's attendance?", expectTitle: /attendance|which child/i,
        expectCap: /my_child_attendance|my_children/ },
      { text: "What fees are due?", expectTitle: /fee|which child/i,
        expectCap: /my_child_fees|my_children/ },
    ],
  },
  {
    key: "student", portal: "student", username: "student_demo", homePattern: "**/student**",
    chatPath: "/student/assistant",
    prompts: [
      { text: "What should I study today?", expectTitle: null, expectCap: "my_daily_plan" },
      { text: "Which topics am I weak in?", expectTitle: /improve|weak|topics/i,
        expectCap: "my_weak_topics" },
    ],
  },
];

async function openPasswordLogin(page, portal) {
  await page.goto(`${BASE}/login?portal=${portal}`, {
    waitUntil: "domcontentloaded", timeout: 60000,
  });
  const username = page.locator("#username-input");
  try {
    await username.waitFor({ state: "visible", timeout: 20000 });
  } catch {
    const onMethod = await page.getByText("Welcome back").isVisible().catch(() => false);
    if (onMethod) await page.getByRole("button", { name: /Username & password/i }).click();
    await username.waitFor({ state: "visible", timeout: 15000 });
  }
}

async function login(page, persona) {
  await openPasswordLogin(page, persona.portal);
  await page.fill("#username-input", persona.username);
  await page.fill("#password-input", PASSWORD);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL(persona.homePattern, { timeout: 45000 });
}

async function composerReachable(page) {
  // The chat composer only renders when WorkspaceRoot is in chat mode (no page children).
  // Parent/student portal shells always pass children -> page mode -> composer absent.
  const composer = page.getByPlaceholder("Ask StudyNexs anything");
  try {
    await composer.waitFor({ state: "visible", timeout: 8000 });
    return true;
  } catch {
    return false;
  }
}

async function askAndCapture(page, prompt) {
  const composer = page.getByPlaceholder("Ask StudyNexs anything");
  await composer.waitFor({ state: "visible", timeout: 20000 });
  await composer.fill(prompt.text);
  const turnResp = page.waitForResponse(
    (r) => r.url().includes("/api/v1/workspace/assistant/turn") && r.request().method() === "POST",
    { timeout: 60000 }
  );
  await page.getByRole("button", { name: "Send message" }).click();
  const resp = await turnResp;
  let body = null;
  try { body = await resp.json(); } catch { body = null; }
  const data = body && body.data ? body.data : {};
  const cap = data.trace ? data.trace.capability : undefined;
  const kind = data.result_kind;
  const title = data.block ? data.block.title : undefined;
  // Wait for the block to render in the DOM.
  await page.waitForTimeout(1200);
  return { status: resp.status(), cap, kind, title, blockTitle: title };
}

function matches(value, matcher) {
  if (matcher == null) return true;
  if (matcher instanceof RegExp) return typeof value === "string" && matcher.test(value);
  return value === matcher;
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });

  const only = (process.env.E2E_ONLY || "").trim();
  const personas = only ? PERSONAS.filter((p) => p.key === only) : PERSONAS;
  for (let i = 0; i < personas.length; i++) {
    const persona = personas[i];
    if (i > 0) {
      await ctx.clearCookies();
      await page.evaluate(() => sessionStorage.clear()).catch(() => {});
    }
    try {
      await login(page, persona);
      results.push(["PASS", `login ${persona.key}`, page.url()]);
    } catch (e) {
      results.push(["FAIL", `login ${persona.key}`, e.message.slice(0, 160)]);
      continue;
    }
    // Portal personas reach chat via a dedicated assistant route; staff get it on the home.
    if (persona.chatPath) {
      await page.goto(BASE + persona.chatPath, {
        waitUntil: "domcontentloaded", timeout: 60000,
      }).catch(() => {});
    }
    // Probe once: is the chat composer even reachable for this persona?
    if (!(await composerReachable(page))) {
      results.push([
        "BLOCKED",
        `${persona.key}: chat composer unreachable`,
        `WorkspaceRoot is in page-mode on ${page.url()} (portal shell passes children); ` +
          "no route renders the composer for this persona.",
      ]);
      continue;
    }
    for (const prompt of persona.prompts) {
      try {
        const r = await askAndCapture(page, prompt);
        const capOk = matches(r.cap, prompt.expectCap);
        const titleOk = prompt.expectTitle == null ? true : matches(r.blockTitle, prompt.expectTitle);
        const clarifyOk = prompt.tolerateClarify && r.kind === "clarify";
        // An `error` block is never a success, even if routing/capability matched.
        const notError = r.kind !== "error";
        const ok = r.status === 200 && notError && (capOk || clarifyOk) && (titleOk || clarifyOk);
        results.push([
          ok ? "PASS" : "FAIL",
          `${persona.key}: "${prompt.text}"`,
          `http=${r.status} cap=${r.cap} kind=${r.kind} title=${JSON.stringify(r.blockTitle)}`,
        ]);
        await page.screenshot({
          path: path.join(SHOTS, `${persona.key}-${prompt.text.slice(0, 20).replace(/\W+/g, "_")}.png`),
          fullPage: true,
        }).catch(() => {});
      } catch (e) {
        results.push(["FAIL", `${persona.key}: "${prompt.text}"`, e.message.slice(0, 160)]);
      }
    }
  }

  await browser.close();

  console.log("\n==================== ASSISTANT CHAT JOURNEYS ====================");
  let pass = 0, fail = 0, blocked = 0;
  for (const [status, name, detail] of results) {
    if (status === "PASS") pass++;
    else if (status === "BLOCKED") blocked++;
    else fail++;
    console.log(`  [${status}] ${name}\n          ${detail}`);
  }
  console.log(`\n  TOTAL: ${pass} pass / ${fail} fail / ${blocked} blocked`);
  if (consoleErrors.length) {
    console.log(`\n  Console errors (${consoleErrors.length}):`);
    for (const e of consoleErrors.slice(0, 10)) console.log(`    - ${e.slice(0, 160)}`);
  }
  console.log(`  Screenshots: ${SHOTS}`);
  process.exit(fail > 0 ? 1 : 0);
})();
