/**
 * P2 browser acceptance against the DISPOSABLE e2e tenant (never the shared reference tenant).
 *
 *   node e2e-p2-acceptance.cjs
 *
 * Reads %TEMP%/studynexs_e2e_fixture.json (written by apps/api/scripts/e2e_fixture.py).
 * Env: E2E_BASE_URL (default http://localhost:3010), E2E_API_URL (default http://127.0.0.1:8010),
 * E2E_OUT (evidence dir). Passwords are never printed.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");

// Same host as the API so the SameSite=lax refresh cookie is sent (ports don't affect same-site).
const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3010";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8010";
const FX = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), "studynexs_e2e_fixture.json"), "utf8"));
if (!/^e2e-/.test(FX.tenant_slug)) throw new Error("Refusing: fixture tenant must start with e2e-");
const OUT = process.env.E2E_OUT || path.join(os.tmpdir(), `sn-p2-acceptance-${Date.now()}`);
fs.mkdirSync(OUT, { recursive: true });

const VIEWPORTS = [
  { name: "1440", width: 1440, height: 900 },
  { name: "768", width: 768, height: 1024 },
  { name: "390", width: 390, height: 844 },
];

const results = [];
const network = [];
const consoleLog = [];

function record(persona, check, ok, detail = "") {
  results.push({ persona, check, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"} [${persona}] ${check}${detail ? ` — ${detail}` : ""}`);
}

async function apiLogin(persona) {
  const p = FX.personas[persona];
  const r = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Tenant-Slug": FX.tenant_slug },
    body: JSON.stringify({ username: p.username, password: p.password }),
  });
  if (!r.ok) throw new Error(`api login ${persona} -> ${r.status}`);
  const body = await r.json();
  return body.access_token || body.data?.access_token;
}

async function apiCall(token, method, url, body) {
  const r = await fetch(`${API}${url}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "X-Tenant-Slug": FX.tenant_slug,
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  let json = null;
  try {
    json = await r.json();
  } catch {
    /* empty */
  }
  return { status: r.status, json };
}

function attach(page, persona) {
  page.on("console", (m) => {
    if (m.type() === "error" || m.type() === "warning") {
      consoleLog.push({ persona, type: m.type(), text: m.text().slice(0, 400), url: page.url() });
    }
  });
  page.on("pageerror", (e) => consoleLog.push({ persona, type: "pageerror", text: e.message, url: page.url() }));
  page.on("response", (res) => {
    const u = res.url();
    if (!u.includes("/api/v1/")) return;
    network.push({ persona, status: res.status(), method: res.request().method(), url: u.replace(API, ""), page: page.url().replace(BASE, "") });
  });
}

async function login(page, persona, portal) {
  const p = FX.personas[persona];
  await page.goto(`${BASE}/login?portal=${portal}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  const user = page.locator("#username-input");
  try {
    await user.waitFor({ state: "visible", timeout: 15000 });
  } catch {
    await page.getByRole("button", { name: /Username & password/i }).click().catch(() => {});
    await user.waitFor({ state: "visible", timeout: 15000 });
  }
  await page.fill("#username-input", p.username);
  await page.fill("#password-input", p.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 45000 });
}

async function settle(page) {
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(500);
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
}

async function noHorizontalOverflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
}

const STATES = {};
const TOKENS = {};
const PORTAL = { parent: "parent", student: "student", student2: "student" };

/** Browser context already signed in as `persona`: one UI login per persona per run. */
async function newPage(browser, persona, vp = VIEWPORTS[0]) {
  const opts = { viewport: { width: vp.width, height: vp.height } };
  if (STATES[persona]) opts.storageState = STATES[persona];
  const ctx = await browser.newContext(opts);
  await ctx.addInitScript(
    ([slug, token]) => {
      sessionStorage.setItem("sn_prospect_tenant_slug", slug);
      if (token && !sessionStorage.getItem("sn_access_token")) sessionStorage.setItem("sn_access_token", token);
    },
    [FX.tenant_slug, TOKENS[persona] || ""]
  );
  const page = await ctx.newPage();
  attach(page, persona);
  if (!STATES[persona]) {
    await login(page, persona, PORTAL[persona] || "staff");
    STATES[persona] = await ctx.storageState();
    TOKENS[persona] = await page.evaluate(() => sessionStorage.getItem("sn_access_token"));
  }
  return { ctx, page };
}

/** Every visible nav control produces a route change (no dead controls). */
async function navSweep(page, persona) {
  const links = await page.locator("nav[aria-label='Main navigation'] a").evaluateAll((as) =>
    as.map((a) => a.getAttribute("href")).filter(Boolean)
  );
  let dead = 0;
  for (const href of [...new Set(links)]) {
    await page.goto(BASE + href, { waitUntil: "domcontentloaded" });
    await settle(page);
    const denied = await page.getByText(/don.t have access|Access denied/i).first().isVisible().catch(() => false);
    if (denied) dead++;
  }
  record(persona, "nav: every item renders (no access-denied, no dead links)", dead === 0, `${links.length} links`);
}

async function chatChecks(page, persona, base) {
  await page.goto(`${BASE}${base}/assistant`, { waitUntil: "domcontentloaded" });
  await settle(page);
  const box = page.getByLabel("Message StudyNexs");
  await box.fill("hello");
  await box.press("Enter");
  await page.waitForURL(new RegExp(`${base}/assistant/c/[0-9a-f-]{36}`), { timeout: 30000 }).catch(() => {});
  const url = page.url();
  const m = /\/assistant\/c\/([0-9a-f-]{36})/.exec(url);
  record(persona, "chat: first turn moves to conversation URL", Boolean(m), url.replace(BASE, ""));
  if (!m) return null;
  await page.reload({ waitUntil: "domcontentloaded" });
  await settle(page);
  const restored = await page.locator(".sn-asst-user__bubble", { hasText: "hello" }).first().isVisible().catch(() => false);
  record(persona, "chat: refresh restores the conversation", restored);
  return m[1];
}

(async () => {
  const browser = await chromium.launch();
  const tokens = {};
  for (const p of Object.keys(FX.personas)) tokens[p] = await apiLogin(p);

  // ── Stage 2 release journey (subject teacher evaluates, incharge releases) ──────────────
  {
    const persona = "teacher";
    const { ctx, page } = await newPage(browser, persona);
    await page.goto(`${BASE}/dashboard/teaching/exams/${FX.exam_id}/evaluate`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await shot(page, "teacher-evaluate-1440");
    await page.getByRole("button", { name: /Ravi Student/ }).click();
    const alreadySuggested = await page.getByText(/Review —/).isVisible().catch(() => false);
    if (!alreadySuggested) {
      for (const [q, a] of [["1", "4"], ["2", "Delhi"], ["3", "Plants make food from sunlight"]]) {
        await page.getByLabel(`Answer for question ${q}`).fill(a);
      }
      await page.getByRole("button", { name: "Evaluate", exact: true }).click();
    }
    await page.getByText(/Review —/).waitFor({ timeout: 90000 });
    await shot(page, "teacher-review-1440");
    for (const cb of await page.getByRole("checkbox", { name: /Acknowledge teacher review/ }).all()) await cb.check();
    await page.getByRole("button", { name: "Approve marks" }).click();
    await page.getByText(/Marks approved and saved/).waitFor({ timeout: 30000 });
    record(persona, "evaluate: subject teacher approves marks (private until release)", true);
    await shot(page, "teacher-approved-1440");

    await page.goto(`${BASE}/dashboard/teaching/exams/${FX.exam_id}/results`, { waitUntil: "domcontentloaded" });
    await settle(page);
    const canRelease = await page.getByRole("button", { name: "Preview release" }).isVisible().catch(() => false);
    record(persona, "release: subject teacher cannot release (P-R1)", !canRelease);
    await ctx.close();
  }

  // Learner sees "pending" before release.
  {
    const r = await apiCall(tokens.student, "GET", `/api/v1/portal/results/${FX.exam_id}`);
    record("student", "API: result pending before release", r.status === 200 && r.json?.data?.status === "pending",
           `status=${r.json?.data?.status}`);
  }

  {
    const persona = "incharge";
    const { ctx, page } = await newPage(browser, persona);
    await page.goto(`${BASE}/dashboard/teaching/exams/${FX.exam_id}/results`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await page.getByRole("button", { name: "Preview release" }).click();
    await page.getByTestId("release-preview").waitFor({ timeout: 15000 });
    await shot(page, "incharge-preview-1440");
    const ack = page.getByRole("checkbox", { name: /pending/ });
    const confirm = page.getByRole("button", { name: "Confirm release" });
    record(persona, "release: partial release blocked until acknowledged",
           (await ack.isVisible()) && (await confirm.isDisabled()));
    await ack.check();
    await confirm.click();
    await page.getByText(/Results released \(generation 1\)/).waitFor({ timeout: 20000 });
    record(persona, "release: incharge confirms generation 1", true);
    await shot(page, "incharge-released-1440");
    const status = await page.getByTestId("release-status").innerText();
    record(persona, "release: status shows Released", /Released/.test(status), status);
    const canWithdraw = await page.getByRole("button", { name: "Withdraw results" }).isVisible().catch(() => false);
    record(persona, "release: incharge has no withdraw (admin/principal only)", !canWithdraw);
    await ctx.close();
  }

  // ── Learner views ───────────────────────────────────────────────────────────────────────
  for (const [persona, portal, url] of [
    ["student", "student", `/student/results/${FX.exam_id}`],
    ["parent", "parent", `/parent/child/${FX.student_id}/results/${FX.exam_id}`],
  ]) {
    for (const vp of VIEWPORTS) {
      const { ctx, page } = await newPage(browser, persona, vp);
      await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
      await settle(page);
      const total = await page.getByTestId("result-total").innerText().catch(() => "");
      record(persona, `results detail shows released total @${vp.name}`, /\d+(\.\d+)?\s*\/\s*6/.test(total), total.trim());
      record(persona, `no horizontal overflow @${vp.name}`, await noHorizontalOverflow(page));
      await shot(page, `${persona}-result-${vp.name}`);
      await ctx.close();
    }
  }
  {
    const r = await apiCall(tokens.student2, "GET", `/api/v1/portal/results/${FX.exam_id}`);
    record("student2", "API: unevaluated student still sees pending", r.json?.data?.status === "pending");
    const x = await apiCall(tokens.parent, "GET", `/api/v1/portal/child/${FX.student2_id}/results`);
    record("parent", "API: parent cannot read another family's child (403/404)", [403, 404].includes(x.status), `${x.status}`);
  }

  // ── Principal: block / unblock with reason; admin: withdraw only ─────────────────────────
  {
    const persona = "principal";
    const { ctx, page } = await newPage(browser, persona);
    await page.goto(`${BASE}/dashboard/teaching/exams/${FX.exam_id}/results`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await page.getByLabel(/Reason \(required/).fill("Board moderation pending");
    await page.getByRole("button", { name: "Block release" }).click();
    await page.getByText(/Blocked by principal/).waitFor({ timeout: 15000 });
    record(persona, "principal blocks results with reason", true);
    const blocked = await apiCall(tokens.student, "GET", `/api/v1/portal/results/${FX.exam_id}`);
    record("student", "API: blocked results hidden from learner", blocked.json?.data?.status === "pending",
           `status=${blocked.json?.data?.status}`);
    await page.getByLabel(/Reason \(required/).fill("Moderation complete");
    await page.getByRole("button", { name: "Unblock" }).click();
    await page.getByText(/^Released/).first().waitFor({ timeout: 15000 });
    record(persona, "principal unblock restores prior state (Released)", true);
    await shot(page, "principal-history-1440");
    await ctx.close();
  }
  {
    const r = await apiCall(tokens.admin, "POST", `/api/v1/exams/${FX.exam_id}/release/preview`);
    record("admin", "API: generic admin cannot release (P-R1)", r.status === 403, `${r.status}`);
    const o = await apiCall(tokens.operations, "GET", `/api/v1/exams/${FX.exam_id}/release`);
    record("operations", "API: operations has no release access", [403, 404].includes(o.status), `${o.status}`);
  }

  // ── Stage 1 shell per persona: home, nav, chat URL refresh, foreign session 404 ─────────
  const staff = [["principal", "staff"], ["admin", "staff"], ["operations", "staff"], ["incharge", "staff"], ["teacher", "staff"]];
  const portals = [["parent", "parent", "/parent"], ["student", "student", "/student"]];
  const sessions = {};
  for (const [persona, portal] of staff) {
    for (const vp of VIEWPORTS) {
      const { ctx, page } = await newPage(browser, persona, vp);
      await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded" });
      await settle(page);
      const homeOk = await page.locator(".sn-home").isVisible().catch(() => false);
      record(persona, `home renders @${vp.name}`, homeOk);
      record(persona, `no horizontal overflow on home @${vp.name}`, await noHorizontalOverflow(page));
      await shot(page, `${persona}-home-${vp.name}`);
      if (vp.name === "390") {
        await page.getByRole("button", { name: "Open menu" }).click();
        const sectionLinks = await page.locator("nav[aria-label='Main navigation'] .sn-rnav__group--secondary a:visible").count();
        record(persona, "mobile: Menu exposes every nav section", sectionLinks >= 1, `${sectionLinks} links`);
        await shot(page, `${persona}-menu-390`);
      }
      if (vp.name === "1440") {
        if (persona === "incharge" || persona === "teacher") {
          const cards = await page.locator("#my-classes .ui-card, #my-classes [class*='card']").count();
          record(persona, "home: My classes lists assigned class", cards >= 1, `${cards}`);
        }
        await navSweep(page, persona);
        sessions[persona] = await chatChecks(page, persona, "/dashboard");
        await shot(page, `${persona}-chat-1440`);
      }
      await ctx.close();
    }
  }
  for (const [persona, portal, base] of portals) {
    const { ctx, page } = await newPage(browser, persona);
    sessions[persona] = await chatChecks(page, persona, base);
    await page.goto(`${BASE}${base}`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await shot(page, `${persona}-home-1440`);
    await ctx.close();
  }

  // Foreign conversation → 404 (API) and "not found" page (browser).
  if (sessions.principal) {
    const r = await apiCall(tokens.teacher, "GET", `/api/v1/workspace/assistant/sessions/${sessions.principal}`);
    record("teacher", "API: another user's conversation is 404", r.status === 404, `${r.status}`);
    const { ctx, page } = await newPage(browser, "teacher");
    await page.goto(`${BASE}/dashboard/assistant/c/${sessions.principal}`, { waitUntil: "domcontentloaded" });
    await settle(page);
    record("teacher", "browser: foreign conversation shows 'Conversation not found'",
           await page.getByText("Conversation not found").isVisible().catch(() => false));
    await shot(page, "teacher-foreign-conversation-1440");
    await ctx.close();
  }

  // Archive / restore via the UI.
  if (sessions.incharge) {
    const { ctx, page } = await newPage(browser, "incharge");
    await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await page.getByRole("button", { name: "Conversations" }).click();
    await page.getByRole("button", { name: /^Archive / }).first().click();
    await page.waitForTimeout(800);
    await page.getByRole("button", { name: "Show archived" }).click();
    const restore = page.getByRole("button", { name: /^Restore / }).first();
    await restore.waitFor({ timeout: 10000 });
    record("incharge", "conversation archived appears under Archived", true);
    await restore.click();
    await page.waitForTimeout(800);
    const list = await apiCall(tokens.incharge, "GET", "/api/v1/workspace/assistant/sessions");
    record("incharge", "restore returns it to the active list",
           (list.json?.data || []).some((s) => s.id === sessions.incharge));
    await shot(page, "incharge-conversations-1440");
    await ctx.close();
  }

  // Ask AI with page context: allowed class vs. another class (server denial).
  {
    const ok = await apiCall(tokens.incharge, "POST", "/api/v1/workspace/assistant/turn", {
      text: "how is this class doing?", page_context: { kind: "class", id: FX.class_id, route: `/dashboard/classes/${FX.class_id}` },
    });
    record("incharge", "Ask AI: own class context accepted", ok.status === 200 && ok.json?.data?.trace?.page_context?.kind === "class");
    const denied = await apiCall(tokens.operations, "POST", "/api/v1/workspace/assistant/turn", {
      text: "how is this class doing?", page_context: { kind: "class", id: FX.class_id },
    });
    record("operations", "Ask AI: class outside scope gets a denied block", denied.json?.data?.block?.kind === "not_found",
           denied.json?.data?.block?.kind);
    const { ctx, page } = await newPage(browser, "incharge");
    await page.goto(`${BASE}/dashboard/classes/${FX.class_id}`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await page.getByRole("button", { name: "Ask AI" }).click();
    const panel = page.getByRole("complementary", { name: "Ask AI" });
    record("incharge", "Ask AI panel opens with class context", await panel.isVisible() && /7 - A/.test(await panel.innerText()));
    await shot(page, "incharge-ask-ai-1440");
    await ctx.close();
  }

  await browser.close();

  const unexpected = network.filter((n) => n.status >= 500 || (n.status >= 400 && ![401, 403, 404, 409].includes(n.status)));
  const errors = consoleLog.filter((c) => c.type === "error" || c.type === "pageerror");
  fs.writeFileSync(path.join(OUT, "results.json"), JSON.stringify(results, null, 2));
  fs.writeFileSync(path.join(OUT, "network.json"), JSON.stringify(network, null, 2));
  fs.writeFileSync(path.join(OUT, "console.json"), JSON.stringify(consoleLog, null, 2));
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} checks passed; ` +
              `${unexpected.length} unexpected API statuses; ${errors.length} console errors; evidence: ${OUT}`);
  for (const u of unexpected.slice(0, 15)) console.log(`  API ${u.status} ${u.method} ${u.url} [${u.persona} @ ${u.page}]`);
  for (const e of errors.slice(0, 15)) console.log(`  CONSOLE [${e.persona}] ${e.text.slice(0, 180)} @ ${e.url.replace(BASE, "")}`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => {
  console.error("HARNESS ERROR:", e);
  process.exit(2);
});
