/**
 * P2 closeout acceptance (items 13/14 + lifecycle, report cards, refresh-token check) against
 * the DISPOSABLE e2e tenant only.
 *
 *   node e2e-p2-closeout.cjs
 *
 * Every browser context performs its OWN UI login (independent refresh cookie chain) — no
 * storage-state or token reuse across contexts. The API must run with
 * AI_DEFAULT_PROVIDER=e2e_scripted (deterministic routing planner; real downstream).
 * Reads %TEMP%/studynexs_e2e_fixture.json. Passwords are never printed.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3010";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8010";
const FX = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), "studynexs_e2e_fixture.json"), "utf8"));
if (!/^e2e-/.test(FX.tenant_slug)) throw new Error("Refusing: fixture tenant must start with e2e-");
const OUT = process.env.E2E_OUT || path.join(os.tmpdir(), `sn-p2-closeout-${Date.now()}`);
fs.mkdirSync(OUT, { recursive: true });

const VIEWPORTS = [
  { name: "1440", width: 1440, height: 900 },
  { name: "768", width: 768, height: 1024 },
  { name: "390", width: 390, height: 844 },
];
const PORTAL = { parent: "parent", student: "student", student2: "student" };

const results = [];
const network = [];
const consoleLog = [];
let ctxSeq = 0;

function record(area, persona, check, ok, detail = "") {
  results.push({ area, persona, check, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"} [${area}/${persona}] ${check}${detail ? ` — ${detail}` : ""}`);
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

function attach(page, persona, ctxId) {
  page.on("console", (m) => {
    if (m.type() === "error") consoleLog.push({ persona, ctxId, type: "error", text: m.text().slice(0, 400), url: page.url() });
  });
  page.on("pageerror", (e) => consoleLog.push({ persona, ctxId, type: "pageerror", text: e.message, url: page.url() }));
  page.on("response", async (res) => {
    const u = res.url();
    if (!u.includes("/api/v1/")) return;
    const entry = { persona, ctxId, status: res.status(), method: res.request().method(), url: u.replace(API, ""), page: page.url().replace(BASE, ""), t: Date.now() };
    if (u.includes("/auth/refresh") && res.status() === 401) {
      entry.detail = await res.text().catch(() => "");
      entry.cookieSent = /studynexs_refresh=/.test(res.request().headers().cookie || "");
    }
    network.push(entry);
  });
}

async function uiLogin(page, persona) {
  const p = FX.personas[persona];
  await page.goto(`${BASE}/login?portal=${PORTAL[persona] || "staff"}`, { waitUntil: "domcontentloaded", timeout: 60000 });
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

/** Fresh, independent browser session: own cookie jar, own login, own refresh chain. */
async function session(browser, persona, vp = VIEWPORTS[0]) {
  const ctxId = `${persona}#${++ctxSeq}`;
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
  await ctx.addInitScript((slug) => sessionStorage.setItem("sn_prospect_tenant_slug", slug), FX.tenant_slug);
  const page = await ctx.newPage();
  attach(page, persona, ctxId);
  await uiLogin(page, persona);
  return { ctx, page, ctxId };
}

async function settle(page) {
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(400);
}
async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
}
async function noOverflow(page) {
  return page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
}
async function go(page, url) {
  await page.goto(BASE + url, { waitUntil: "domcontentloaded" });
  await settle(page);
}

/** Send a chat message from the current conversation page; returns the last block's text. */
async function ask(page, text) {
  const before = await page.locator(".sn-asst-turns > *").count();
  const box = page.getByLabel("Message StudyNexs");
  await box.fill(text);
  await box.press("Enter");
  await page.locator(".sn-asst-turns > *").nth(before + 1).waitFor({ timeout: 45000 }).catch(() => {});
  await page.locator(".sn-asst-thinking").waitFor({ state: "detached", timeout: 45000 }).catch(() => {});
  await settle(page);
  const blocks = page.locator(".sn-asst-turns > :not(.sn-asst-user)");
  return (await blocks.last().innerText().catch(() => "")).replace(/\s+/g, " ").trim();
}

// ── Chat prompts per persona: three permitted + one denied (deterministic planner phrases) ──
const CHAT = {
  principal: {
    base: "/dashboard",
    allowed: [["school overview", /Students|Teachers|Classes/i], ["students in 7-A", /Ravi Student/], ["fee collection", /Collected|Pending|fee/i]],
    denied: null,
  },
  admin: {
    base: "/dashboard",
    allowed: [["school overview", /Students|Teachers/i], ["staff directory", /Tara Teacher|Ila Incharge/], ["fee collection", /Collected|Pending|fee/i]],
    denied: null,
  },
  incharge: {
    base: "/dashboard",
    allowed: [["students in 7-A", /Ravi Student/], ["attendance today in 7-A", /attendance|present|marked/i], ["low attendance students", /attendance|No students|students/i]],
    denied: ["fee collection", /isn.t available for your role|Fees/i],
  },
  teacher: {
    base: "/dashboard",
    allowed: [["school overview", /Students|Classes/i], ["low attendance students", /attendance|students/i], ["profile of Ravi", /Ravi|Not available|access/i]],
    denied: ["fee collection", /isn.t available for your role/i],
  },
  operations: {
    base: "/dashboard",
    allowed: [["school overview", /Students|Classes/i], ["staff directory", /Tara|Ila|Staff/i], ["low attendance students", /attendance|students/i]],
    denied: ["fee collection", /isn.t available for your role/i],
  },
  parent: {
    base: "/parent",
    allowed: [["my children", /Ravi/], ["my child's attendance", /attendance|Ravi/i], ["my child's progress", /Ravi|progress|topic|No /i]],
    denied: ["staff directory", /isn.t available for your role/i],
  },
  student: {
    base: "/student",
    allowed: [["my daily plan", /plan|study|No learning|lesson/i], ["my weak topics", /topic|sample|No /i], ["my lesson", /lesson|Lesson|tutor|No /i]],
    denied: ["fee collection", /isn.t available for your role/i],
  },
};

(async () => {
  const browser = await chromium.launch();
  const tok = {};
  for (const p of Object.keys(FX.personas)) tok[p] = await apiLogin(p);

  // ── Item 14: chat workflows ───────────────────────────────────────────────────────────────
  const convo = {};
  for (const [persona, spec] of Object.entries(CHAT)) {
    const { ctx, page } = await session(browser, persona);
    await go(page, `${spec.base}/assistant`);
    let i = 0;
    for (const [text, expect] of spec.allowed) {
      const out = await ask(page, text);
      const deniedish = /isn.t available for your role|I can take you to the right place/i.test(out);
      record("chat", persona, `permitted: "${text}"`, expect.test(out) && !deniedish, out.slice(0, 140));
      if (i++ === 0) {
        const m = /\/assistant\/c\/([0-9a-f-]{36})/.exec(page.url());
        record("chat", persona, "first turn moves to /assistant/c/{id}", Boolean(m), page.url().replace(BASE, ""));
        convo[persona] = m && m[1];
      }
    }
    if (spec.denied) {
      const out = await ask(page, spec.denied[0]);
      record("chat", persona, `denied: "${spec.denied[0]}"`, spec.denied[1].test(out), out.slice(0, 140));
    }
    await shot(page, `chat-${persona}-1440`);
    // Refresh restores the full conversation (all user turns).
    const turnsBefore = await page.locator(".sn-asst-user__bubble").count();
    await page.reload({ waitUntil: "domcontentloaded" });
    await settle(page);
    const turnsAfter = await page.locator(".sn-asst-user__bubble").count();
    record("chat", persona, "refresh restores every turn", turnsAfter === turnsBefore && turnsBefore > 0, `${turnsBefore}→${turnsAfter}`);
    await ctx.close();
  }

  // "Show my timetable" → Back to conversation (staff + both portals).
  for (const [persona, base] of [["incharge", "/dashboard"], ["parent", "/parent"], ["student", "/student"]]) {
    const { ctx, page } = await session(browser, persona);
    await go(page, `${base}/assistant`);
    await ask(page, "hello");
    const sid = (/\/assistant\/c\/([0-9a-f-]{36})/.exec(page.url()) || [])[1];
    const out = await ask(page, "Show my timetable");
    record("chat", persona, "\"Show my timetable\" answers with a navigate block", /Opening|Timetable/i.test(out), out.slice(0, 100));
    await page.getByRole("button", { name: "Open", exact: true }).last().click();
    await page.waitForURL(/timetable/, { timeout: 20000 }).catch(() => {});
    await settle(page);
    const onTimetable = /timetable/.test(page.url());
    const hasFrom = /from=c%2F[0-9a-f-]{36}/.test(page.url());
    const denied = await page.getByText(/don.t have access|Access denied/i).first().isVisible().catch(() => false);
    record("chat", persona, "Open navigates to timetable carrying ?from=c/{id}", onTimetable && hasFrom, page.url().replace(BASE, ""));
    record("chat", persona, "timetable page renders for this role (no access-denied)", onTimetable && !denied);
    await shot(page, `timetable-${persona}-1440`);
    const back = page.getByTestId("back-to-conversation");
    const backVisible = await back.isVisible().catch(() => false);
    record("chat", persona, "\"Back to conversation\" chip visible", backVisible);
    if (backVisible) {
      await back.click();
      await page.waitForURL(new RegExp(`/assistant/c/${sid}`), { timeout: 20000 }).catch(() => {});
      await settle(page);
      const kept = await page.locator(".sn-asst-user__bubble", { hasText: "Show my timetable" }).isVisible().catch(() => false);
      record("chat", persona, "Back returns to the same conversation with history", page.url().includes(sid) && kept, page.url().replace(BASE, ""));
    }
    // Conversation survives in-app navigation: go elsewhere, return via URL.
    await go(page, base === "/dashboard" ? "/dashboard/classes" : base);
    await go(page, `${base}/assistant/c/${sid}`);
    const still = await page.locator(".sn-asst-user__bubble", { hasText: "hello" }).isVisible().catch(() => false);
    record("chat", persona, "conversation URL reopens after navigating away", still);
    await ctx.close();
  }

  // Record drawer from an actual chat result + Ask AI context preserved.
  {
    const persona = "incharge";
    const { ctx, page } = await session(browser, persona);
    await go(page, `/dashboard/classes/${FX.class_id}`);
    await page.getByRole("button", { name: "Ask AI" }).click();
    const panel = page.getByRole("complementary", { name: "Ask AI" });
    const ctxBar = panel.getByRole("group", { name: "Conversation context" });
    record("chat", persona, "Ask AI on class page shows the class in the context bar",
           (await ctxBar.isVisible().catch(() => false)) && /7\s*-\s*A/.test(await ctxBar.innerText().catch(() => "")));
    const box = panel.getByLabel("Message StudyNexs");
    await box.fill("students in 7-A");
    await box.press("Enter");
    await panel.getByText(/Ravi Student/).first().waitFor({ timeout: 45000 }).catch(() => {});
    const answer = await panel.innerText().catch(() => "");
    record("chat", persona, "Ask AI answer grounded in the page's class", /Ravi Student/.test(answer));
    await shot(page, "askai-class-1440");
    // Drawer: the shipped trigger is a chat-produced record link. Rows carry no record links
    // (backend emits none), so assert honestly whether any record link exists in the answer.
    const rowLink = panel.locator("button[data-record-href]").first();
    const hasLink = await rowLink.isVisible().catch(() => false);
    let drawerOk = false;
    if (hasLink) {
      await rowLink.click();
      const drawer = page.getByRole("dialog", { name: "Student summary" });
      await drawer.waitFor({ timeout: 15000 }).catch(() => {});
      await drawer.getByLabel("Loading").waitFor({ state: "detached", timeout: 20000 }).catch(() => {});
      await drawer.getByText(/Ravi Student/).first().waitFor({ timeout: 10000 }).catch(() => {});
      const txt = await drawer.innerText().catch(() => "");
      drawerOk = /Ravi Student/.test(txt) && (await drawer.getByRole("link", { name: /Open full page/ }).isVisible().catch(() => false));
      await shot(page, "record-drawer-1440");
      await drawer.getByRole("button", { name: "Close" }).click().catch(() => {});
      record("chat", persona, "drawer closes and conversation remains", await panel.getByText(/Ravi Student/).first().isVisible().catch(() => false));
    }
    record("chat", persona, "record drawer opens from a chat result row (Student summary + Open full page)", drawerOk,
           hasLink ? "" : "no record link rendered");
    await ctx.close();
  }

  // ── Item 13: principal KPI cross-check against /dashboard/summary ───────────────────────────
  {
    const persona = "principal";
    const sum = (await apiCall(tok.principal, "GET", "/api/v1/dashboard/summary")).json?.data || {};
    const fees = (await apiCall(tok.principal, "GET", "/api/v1/fees/stats")).json?.data || {};
    const { ctx, page } = await session(browser, persona);
    await go(page, "/dashboard");
    await page.waitForTimeout(2500); // CountUp settles
    const kpis = await page.locator(".briefing-exec-kpi").evaluateAll((els) =>
      els.map((e) => ({
        label: (e.querySelector(".briefing-exec-kpi-label")?.textContent || "").trim(),
        value: (e.querySelector(".briefing-exec-kpi-value")?.textContent || "").trim(),
      }))
    );
    fs.writeFileSync(path.join(OUT, "principal-kpis.json"), JSON.stringify({ ui: kpis, summary: sum, fees }, null, 2));
    const val = (l) => (kpis.find((k) => k.label === l) || {}).value || "";
    const digits = (s) => (s.match(/[0-9]+/g) || []).join("");
    record("kpi", persona, "Students = summary.total_students", digits(val("Students")) === String(sum.total_students ?? 0),
           `ui=${val("Students")} api=${sum.total_students}`);
    record("kpi", persona, "Admissions = summary.admissions_pipeline", digits(val("Admissions")) === String(sum.admissions_pipeline ?? 0),
           `ui=${val("Admissions")} api=${sum.admissions_pipeline}`);
    const att = sum.school_attendance_status === "not_recorded" || sum.school_attendance_percent == null
      ? "—" : `${Math.round(sum.school_attendance_percent)}%`;
    record("kpi", persona, "Present today = summary attendance", val("Present today") === att, `ui=${val("Present today")} api=${att}`);
    record("kpi", persona, "Fees collected = /fees/stats total_collected",
           digits(val("Fees collected")) === String(Math.round(fees.total_collected ?? 0)), `ui=${val("Fees collected")} api=${fees.total_collected}`);
    await shot(page, "principal-home-kpis-1440");
    await ctx.close();
  }

  // ── Items 13/14: parent + student navigation at three widths ────────────────────────────────
  for (const persona of ["parent", "student"]) {
    for (const vp of VIEWPORTS) {
      const { ctx, page } = await session(browser, persona, vp);
      await go(page, persona === "parent" ? "/parent" : "/student");
      if (vp.name === "390") {
        const openMenu = page.getByRole("button", { name: "Open menu" });
        if (await openMenu.isVisible().catch(() => false)) await openMenu.click();
      }
      const hrefs = [...new Set(await page.locator("nav[aria-label='Main navigation'] a").evaluateAll((as) =>
        as.map((a) => a.getAttribute("href")).filter(Boolean)))];
      let bad = [];
      for (const href of hrefs) {
        await go(page, href);
        const denied = await page.getByText(/don.t have access|Access denied|Something went wrong/i).first().isVisible().catch(() => false);
        if (denied || !(await noOverflow(page))) bad.push(href);
      }
      record("nav", persona, `every nav item renders, no overflow @${vp.name}`, hrefs.length > 0 && bad.length === 0,
             `${hrefs.length} items${bad.length ? `; bad: ${bad.join(",")}` : ""}`);
      await go(page, persona === "parent" ? "/parent" : "/student");
      await shot(page, `${persona}-home-${vp.name}`);
      await ctx.close();
    }
  }

  // ── A. Complete results lifecycle on the second exam (browser-driven) ───────────────────────
  const LX = FX.lifecycle_exam_id;
  const learnerMarks = async () => (await apiCall(tok.student, "GET", `/api/v1/portal/results/${LX}`)).json?.data;
  const notifCount = async (who) => ((await apiCall(tok[who], "GET", "/api/v1/notifications")).json?.data || [])
    .filter((n) => /E2E Lifecycle Test/.test(`${n.title} ${n.message || n.body || ""}`)).length;

  async function evaluateInBrowser(page, studentName, answers) {
    await go(page, `/dashboard/teaching/exams/${LX}/evaluate`);
    await page.getByRole("button", { name: new RegExp(studentName) }).click();
    for (const [q, a] of answers) await page.getByLabel(`Answer for question ${q}`).fill(a);
    await page.getByRole("button", { name: "Evaluate", exact: true }).click();
    await page.getByText(/Review —/).waitFor({ timeout: 90000 });
    for (const cb of await page.getByRole("checkbox", { name: /Acknowledge teacher review/ }).all()) await cb.check();
    await page.getByRole("button", { name: "Approve marks" }).click();
    await page.getByText(/Marks approved and saved/).waitFor({ timeout: 30000 });
  }
  async function releaseInBrowser(page, partial) {
    await go(page, `/dashboard/teaching/exams/${LX}/results`);
    await page.getByRole("button", { name: "Preview release" }).click();
    await page.getByTestId("release-preview").waitFor({ timeout: 15000 });
    const gen = (await page.getByTestId("release-preview").innerText()).match(/generation (\d+)/)?.[1];
    if (partial) await page.getByRole("checkbox", { name: /pending/ }).check();
    await page.getByRole("button", { name: "Confirm release" }).click();
    await page.getByText(/Results released \(generation \d+\)|Nothing new to release/).waitFor({ timeout: 20000 });
    return gen;
  }

  {
    const t = await session(browser, "teacher");
    const ic = await session(browser, "incharge");
    // 1. Initial approval creates a version; learner still pending; no learner notification.
    await evaluateInBrowser(t.page, "Ravi Student", [["1", "4"], ["2", "Delhi"], ["3", "no idea"]]);
    const versionsAfter1 = (await apiCall(tok.incharge, "GET", `/api/v1/exams/${LX}/submissions`)).json?.data || [];
    const ravi = versionsAfter1.find((s) => s.student_id === FX.student_id) || {};
    record("lifecycle", "teacher", "approval creates version v1 (not published)", ravi.latest_version_no === 1 && !ravi.published_version_no,
           `latest=${ravi.latest_version_no} published=${ravi.published_version_no}`);
    record("lifecycle", "student", "unreleased → learner sees pending", (await learnerMarks())?.status === "pending");
    const n0 = await notifCount("student");
    record("lifecycle", "student", "no notification before release", n0 === 0, `${n0}`);
    // 2. Generation 1 (partial: Sita pending).
    const g1 = await releaseInBrowser(ic.page, true);
    record("lifecycle", "incharge", "generation 1 released (partial)", g1 === "1", `gen=${g1}`);
    const v1 = (await learnerMarks())?.marks_obtained;
    record("lifecycle", "student", "gen 1 visible to learner", v1 != null, `marks=${v1}`);
    const n1s = await notifCount("student"), n1p = await notifCount("parent");
    record("lifecycle", "student+parent", "one notification each for gen 1", n1s === 1 && n1p === 1, `student=${n1s} parent=${n1p}`);
    // 3. Late approval (Sita) → explicit gen 2.
    await evaluateInBrowser(t.page, "Sita Student", [["1", "4"], ["2", "Delhi"], ["3", "Plants make food from sunlight"]]);
    const g2 = await releaseInBrowser(ic.page, false);
    record("lifecycle", "incharge", "late approval → explicit generation 2", g2 === "2", `gen=${g2}`);
    record("lifecycle", "student", "gen 2 does not change Ravi's visible marks", (await learnerMarks())?.marks_obtained === v1);
    record("lifecycle", "student", "no duplicate notification for Ravi on gen 2", (await notifCount("student")) === 1);
    // 4. Changed marks → new immutable version; old version stays visible until re-release.
    const subs = (await apiCall(tok.incharge, "GET", `/api/v1/exams/${LX}/submissions`)).json?.data || [];
    const evalId = (subs.find((s) => s.student_id === FX.student_id) || {}).evaluation_id;
    const re = await apiCall(tok.incharge, "POST", `/api/v1/exams/evaluations/${evalId}/reopen`, { reason: "Recheck Q3" });
    record("lifecycle", "incharge", "reopen approved evaluation", re.status === 200, `${re.status}`);
    await go(ic.page, `/dashboard/teaching/exams/${LX}/evaluate`);
    await ic.page.getByRole("button", { name: /Ravi Student/ }).click();
    await ic.page.getByText(/Review —/).waitFor({ timeout: 60000 });
    const q3 = ic.page.getByLabel("Final marks for question 3");
    const q3Ok = await q3.isVisible().catch(() => false);
    record("lifecycle", "incharge", "reopened sheet offers editable final marks (labelled)", q3Ok);
    if (q3Ok) {
      await q3.fill("2");
      await ic.page.getByPlaceholder("Example: Accepted alternate method").first().fill("Partial credit on recheck");
    }
    for (const cb of await ic.page.getByRole("checkbox", { name: /Acknowledge teacher review/ }).all()) await cb.check();
    await ic.page.getByRole("button", { name: "Approve marks" }).click();
    await ic.page.getByText(/Marks approved and saved/).waitFor({ timeout: 30000 }).catch(() => {});
    const after = ((await apiCall(tok.incharge, "GET", `/api/v1/exams/${LX}/submissions`)).json?.data || [])
      .find((s) => s.student_id === FX.student_id) || {};
    record("lifecycle", "incharge", "changed marks create a new immutable version", after.latest_version_no >= 2 && after.changed_since_release === true,
           `latest=${after.latest_version_no} published=${after.published_version_no} changed=${after.changed_since_release}`);
    record("lifecycle", "student", "previous published marks stay visible until re-release", (await learnerMarks())?.marks_obtained === v1);
    // 5. Explicit re-release (gen 3) and history.
    const g3 = await releaseInBrowser(ic.page, false);
    const v3 = (await learnerMarks())?.marks_obtained;
    record("lifecycle", "incharge", "explicit re-release → generation 3", g3 === "3", `gen=${g3}`);
    record("lifecycle", "student", "learner now sees the new version", v3 != null && v3 !== v1, `v1=${v1} v3=${v3}`);
    const n3 = await notifCount("student");
    record("lifecycle", "student", "exactly one new notification for the genuine re-release", n3 === 2, `${n3}`);
    await go(ic.page, `/dashboard/teaching/exams/${LX}/results`);
    const hist = await ic.page.locator("table.data-table").innerText();
    record("lifecycle", "incharge", "history lists gen 1, 2, 3", /gen 1/.test(hist) && /gen 2/.test(hist) && /gen 3/.test(hist));
    await shot(ic.page, "lifecycle-history-1440");
    // 6. Withdraw (admin) → hidden; restore by explicit re-release (principal).
    const ad = await session(browser, "admin");
    await go(ad.page, `/dashboard/teaching/exams/${LX}/results`);
    await ad.page.getByLabel(/Reason \(required/).fill("Marks entry error");
    await ad.page.getByRole("button", { name: "Withdraw results" }).click();
    await ad.page.getByText(/Withdrawn/).first().waitFor({ timeout: 15000 });
    record("lifecycle", "admin", "admin withdraws with reason", true);
    record("lifecycle", "student", "withdrawn → learner sees pending", (await learnerMarks())?.status === "pending");
    const nW = await notifCount("student");
    const pr = await session(browser, "principal");
    const g4 = await releaseInBrowser(pr.page, false);
    record("lifecycle", "principal", "restore via explicit re-release (generation 4)", g4 === "4", `gen=${g4}`);
    record("lifecycle", "student", "restored results visible again", (await learnerMarks())?.marks_obtained === v3);
    record("lifecycle", "student", "restore notifies once (no duplicates)", (await notifCount("student")) === nW + 1, `${nW}→${await notifCount("student")}`);
    await shot(pr.page, "lifecycle-restored-1440");
    for (const s of [t, ic, ad, pr]) await s.ctx.close();
  }

  // ── 3. Learner report card (generated + approved by incharge on released results) ───────────
  {
    const gen = await apiCall(tok.incharge, "POST", "/api/v1/ai/report-cards/generate",
                              { student_id: FX.student_id, title: "Term 1 Report" });
    record("reportcard", "incharge", "generate report card", gen.status === 200, `${gen.status}`);
    const rid = gen.json?.id;
    const preApprove = (await apiCall(tok.student, "GET", "/api/v1/portal/report-cards")).json?.data || [];
    record("reportcard", "student", "draft card hidden from learner", !preApprove.some((c) => c.id === rid));
    const ap = await apiCall(tok.incharge, "POST", `/api/v1/ai/report-cards/${rid}/approve`);
    record("reportcard", "incharge", "approve report card", ap.status === 200, `${ap.status}`);
    for (const [persona, url] of [
      ["student", `/student/results`],
      ["parent", `/parent/child/${FX.student_id}/results`],
    ]) {
      for (const vp of VIEWPORTS) {
        const { ctx, page } = await session(browser, persona, vp);
        await go(page, url);
        const row = page.getByTestId("report-card-row").first();
        const listed = await row.isVisible().catch(() => false);
        record("reportcard", persona, `card listed on Results @${vp.name}`, listed);
        if (listed) {
          await row.click();
          await page.getByTestId("report-card-total").waitFor({ timeout: 15000 }).catch(() => {});
          const total = await page.getByTestId("report-card-total").innerText().catch(() => "");
          record("reportcard", persona, `card detail shows published totals @${vp.name}`, /\d/.test(total), total.trim());
          record("reportcard", persona, `no overflow @${vp.name}`, await noOverflow(page));
          await shot(page, `reportcard-${persona}-${vp.name}`);
        }
        await ctx.close();
      }
    }
    // Unreleased change → card figures stay on the published version and remark is withheld.
    const subs = (await apiCall(tok.incharge, "GET", `/api/v1/exams/${LX}/submissions`)).json?.data || [];
    const evalId = (subs.find((s) => s.student_id === FX.student_id) || {}).evaluation_id;
    const cardBefore = (await apiCall(tok.student, "GET", `/api/v1/portal/report-cards/${rid}`)).json?.data;
    await apiCall(tok.incharge, "POST", `/api/v1/exams/evaluations/${evalId}/reopen`, { reason: "Second recheck" });
    await apiCall(tok.incharge, "POST", `/api/v1/exams/evaluations/${evalId}/approve`,
                  { teacher_overrides: { 3: { marks: 3, reason: "full credit" } }, correction_summary: "Full credit" });
    const regen = await apiCall(tok.incharge, "POST", "/api/v1/ai/report-cards/generate",
                                { student_id: FX.student_id, title: "Term 1 Report (rev)" });
    await apiCall(tok.incharge, "POST", `/api/v1/ai/report-cards/${regen.json?.id}/approve`);
    const revCard = (await apiCall(tok.student, "GET", `/api/v1/portal/report-cards/${regen.json?.id}`)).json?.data;
    record("reportcard", "student", "card built on unreleased marks shows PUBLISHED figures only",
           revCard && cardBefore && revCard.total_obtained === cardBefore.total_obtained && revCard.remark_withheld === true,
           `published=${cardBefore?.total_obtained} shown=${revCard?.total_obtained} withheld=${revCard?.remark_withheld}`);
    const x = await apiCall(tok.parent, "GET", `/api/v1/portal/child/${FX.student2_id}/report-cards`);
    record("reportcard", "parent", "other family's report cards denied", [403, 404].includes(x.status), `${x.status}`);
  }

  // ── 4. Search scope (incharge) ─────────────────────────────────────────────────────────────
  {
    const r = await apiCall(tok.incharge, "GET", "/api/v1/academic/students?search=Student&page_size=50");
    const names = (r.json?.items || []).map((s) => s.student_name).sort();
    record("search", "incharge", "incharge search covers all own classes (server-scoped)", r.status === 200 && names.includes("Ravi Student"), names.join(","));
    const t = await apiCall(tok.teacher, "GET", "/api/v1/academic/students?search=Student");
    record("search", "teacher", "subject teacher has no roster search", t.status === 403, `${t.status}`);
    const st = await apiCall(tok.teacher, "GET", "/api/v1/users?search=Ila");
    record("search", "teacher", "staff search stays manager-only", st.status === 403, `${st.status}`);
    const { ctx, page } = await session(browser, "incharge");
    await go(page, "/dashboard");
    await page.getByRole("button", { name: "Open search" }).click();
    const combo = page.getByRole("combobox");
    await combo.waitFor({ timeout: 10000 });
    await combo.fill("Ravi");
    const hit = page.locator(".topbar-search-combobox").getByText("Ravi Student").first();
    await hit.waitFor({ timeout: 15000 }).catch(() => {});
    record("search", "incharge", "⌘K search finds own-class student", await hit.isVisible().catch(() => false));
    await shot(page, "search-incharge-1440");
    await ctx.close();
  }

  await browser.close();

  // ── Refresh-token analysis: every 401 on /auth/refresh, per independent context ─────────────
  const refresh = network.filter((n) => n.url.includes("/auth/refresh"));
  const refresh401 = refresh.filter((n) => n.status === 401);
  fs.writeFileSync(path.join(OUT, "refresh-analysis.json"), JSON.stringify({ total: refresh.length, r401: refresh401 }, null, 2));

  const unexpected = network.filter((n) => n.status >= 500 || (n.status >= 400 && ![401, 403, 404, 409].includes(n.status)));
  const other401 = network.filter((n) => n.status === 401 && !n.url.includes("/auth/refresh"));
  const errors = consoleLog.filter((c) => c.type === "error" || c.type === "pageerror");
  fs.writeFileSync(path.join(OUT, "results.json"), JSON.stringify(results, null, 2));
  fs.writeFileSync(path.join(OUT, "network.json"), JSON.stringify(network, null, 2));
  fs.writeFileSync(path.join(OUT, "console.json"), JSON.stringify(consoleLog, null, 2));
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} checks passed; contexts=${ctxSeq}; ` +
              `refresh calls=${refresh.length} (401=${refresh401.length}); other 401=${other401.length}; ` +
              `unexpected API=${unexpected.length}; console errors=${errors.length}; evidence: ${OUT}`);
  for (const r of refresh401.slice(0, 20)) console.log(`  REFRESH 401 [${r.ctxId}] cookieSent=${r.cookieSent} ${r.detail} @ ${r.page}`);
  for (const u of unexpected.slice(0, 15)) console.log(`  API ${u.status} ${u.method} ${u.url} [${u.ctxId} @ ${u.page}]`);
  for (const e of errors.slice(0, 15)) console.log(`  CONSOLE [${e.ctxId}] ${e.text.slice(0, 180)} @ ${e.url.replace(BASE, "")}`);
  for (const f of failed) console.log(`  FAILED [${f.area}/${f.persona}] ${f.check} ${f.detail}`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => {
  console.error("HARNESS ERROR:", e);
  process.exit(2);
});
