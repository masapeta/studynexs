/**
 * Final acceptance checks (disposable e2e tenant; API with AI_DEFAULT_PROVIDER=e2e_scripted):
 *  1. Successful answer → genuine contextual follow-up (entity inherited server-side).
 *  2. "Open assessments" → landed page keeps ?from → Back to conversation.
 *  3. Student record drawer from a real chat result; authorization + conversation preserved.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3010";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8010";
const FX = JSON.parse(fs.readFileSync(path.join(os.tmpdir(), "studynexs_e2e_fixture.json"), "utf8"));
if (!/^e2e-/.test(FX.tenant_slug)) throw new Error("Refusing: fixture tenant must start with e2e-");
const OUT = process.env.E2E_OUT || path.join(os.tmpdir(), `sn-final-${Date.now()}`);
fs.mkdirSync(OUT, { recursive: true });

const results = [];
const errors = [];
const network = [];
function record(n, check, ok, detail = "") {
  results.push({ n, check, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"} [${n}] ${check}${detail ? ` — ${detail}` : ""}`);
}
async function settle(page) {
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(400);
}
async function session(browser, persona) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.addInitScript((slug) => sessionStorage.setItem("sn_prospect_tenant_slug", slug), FX.tenant_slug);
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(`${persona}: ${e.message}`));
  page.on("console", (m) => m.type() === "error" && errors.push(`${persona}: ${m.text()}`));
  page.on("response", (r) => r.url().includes("/api/v1/") && network.push({ persona, status: r.status(), url: r.url().replace(API, "") }));
  const p = FX.personas[persona];
  const portal = { parent: "parent", student: "student", student2: "student" }[persona] || "staff";
  await page.goto(`${BASE}/login?portal=${portal}`, { waitUntil: "domcontentloaded" });
  await page.locator("#username-input").waitFor({ timeout: 15000 }).catch(async () => {
    await page.getByRole("button", { name: /Username & password/i }).click();
  });
  await page.fill("#username-input", p.username);
  await page.fill("#password-input", p.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 45000 });
  return { ctx, page };
}
async function ask(page, text) {
  const before = await page.locator(".sn-asst-turns > *").count();
  const box = page.getByLabel("Message StudyNexs");
  await box.fill(text);
  await box.press("Enter");
  await page.locator(".sn-asst-turns > *").nth(before + 1).waitFor({ timeout: 45000 }).catch(() => {});
  await page.locator(".sn-asst-thinking").waitFor({ state: "detached", timeout: 45000 }).catch(() => {});
  await settle(page);
  return (await page.locator(".sn-asst-turns > :not(.sn-asst-user)").last().innerText().catch(() => "")).replace(/\s+/g, " ").trim();
}
const sidOf = (url) => (/\/assistant\/c\/([0-9a-f-]{36})/.exec(url) || [])[1];

(async () => {
  const browser = await chromium.launch();

  // ── 1 + 2: incharge — results, follow-up, then "Open assessments" ─────────────────────
  {
    const { ctx, page } = await session(browser, "incharge");
    await page.goto(`${BASE}/dashboard/assistant`, { waitUntil: "domcontentloaded" });
    await settle(page);
    const first = await ask(page, "attendance of Ravi");
    const sid = sidOf(page.url());
    record(1, "first turn answers successfully (student attendance)", /Attendance — Ravi Student/.test(first) && !/right place|isn.t available/i.test(first), first.slice(0, 110));
    const follow = await ask(page, "and his marks?");
    record(1, "follow-up names no student yet answers for Ravi (context inherited)",
      /Ravi Student/.test(follow) && /Marks|Exam|marks/i.test(follow) && !/right place|Which student|not found/i.test(follow), follow.slice(0, 140));
    const turn = await fetch(`${API}/api/v1/workspace/assistant/sessions/${sid}`, {
      headers: { "X-Tenant-Slug": FX.tenant_slug, Authorization: `Bearer ${await page.evaluate(() => sessionStorage.getItem("sn_access_token"))}` },
    }).then((r) => r.json()).catch(() => null);
    const msgs = Array.isArray(turn?.data) ? turn.data : turn?.data?.messages || [];
    const lastSem = [...msgs].reverse().find((m) => m.role === "assistant" && m.semantic_state)?.semantic_state;
    record(1, "server semantic state carries the inherited student",
      lastSem?.capability === "student_marks" && Boolean(lastSem?.entities?.student), JSON.stringify(lastSem?.entities || {}));
    const bar = page.getByRole("group", { name: "Conversation context" });
    record(1, "context bar reflects the carried subject", /Ravi|student/i.test(await bar.innerText().catch(() => "")), (await bar.innerText().catch(() => "")).replace(/\s+/g, " "));
    await page.screenshot({ path: path.join(OUT, "1-follow-up.png"), fullPage: true });

    // 2. "Open assessments"
    const res = await ask(page, "class results for 7-A");
    record(2, "class results answer offers \"Open assessments\"", await page.getByRole("button", { name: "Open assessments" }).last().isVisible().catch(() => false), res.slice(0, 90));
    await page.getByRole("button", { name: "Open assessments" }).last().click();
    await page.waitForURL(/\/dashboard\/teaching\/exams/, { timeout: 20000 }).catch(() => {});
    await settle(page);
    record(2, "lands on Assessments with ?from=c/{id}", /\/dashboard\/teaching\/exams\?from=c%2F[0-9a-f-]{36}/.test(page.url()), page.url().replace(BASE, ""));
    const denied = await page.getByText(/don.t have access|Access denied/i).first().isVisible().catch(() => false);
    record(2, "assessments page renders for the incharge", !denied);
    const back = page.getByTestId("back-to-conversation");
    record(2, "\"Back to conversation\" chip visible", await back.isVisible({ timeout: 10000 }).catch(() => false));
    await page.screenshot({ path: path.join(OUT, "2-open-assessments.png"), fullPage: true });
    await back.click();
    await page.waitForURL(new RegExp(`/assistant/c/${sid}`), { timeout: 20000 }).catch(() => {});
    await settle(page);
    const kept = await page.locator(".sn-asst-user__bubble").allInnerTexts();
    record(2, "returns to the same conversation with all three turns",
      page.url().includes(sid) && ["attendance of Ravi", "and his marks?", "class results for 7-A"].every((t) => kept.some((k) => k.includes(t))), kept.join(" | "));
    await ctx.close();
  }

  // ── 3: record drawer from a real chat result; authorization; conversation preserved ────
  {
    const { ctx, page } = await session(browser, "incharge");
    await page.goto(`${BASE}/dashboard/assistant`, { waitUntil: "domcontentloaded" });
    await settle(page);
    await ask(page, "students in 7-A");
    const sid = sidOf(page.url());
    // First cell (admission no) is the record link; pick the row that belongs to Ravi.
    const row = page.locator("tr", { hasText: "Ravi Student" }).locator("button[data-record-href^='/dashboard/students/']").first();
    record(3, "chat result row is a record link", await row.isVisible().catch(() => false));
    const href = await row.getAttribute("data-record-href");
    const studentId = (href || "").split("/").pop();
    await row.click();
    const drawer = page.getByRole("dialog", { name: "Student summary" });
    await drawer.waitFor({ timeout: 15000 }).catch(() => {});
    await drawer.getByLabel("Loading").waitFor({ state: "detached", timeout: 20000 }).catch(() => {});
    const txt = await drawer.innerText().catch(() => "");
    record(3, "drawer shows the student's authorised summary", /Ravi Student/.test(txt) && studentId === FX.student_id, txt.replace(/\s+/g, " ").slice(0, 100));
    const profileCall = network.find((n) => n.persona === "incharge" && n.url.includes(`/academic/students/${studentId}/profile`));
    record(3, "drawer data came from the authorised profile endpoint (200)", profileCall?.status === 200, profileCall ? `${profileCall.status} ${profileCall.url}` : "no call");
    record(3, "drawer stays on the conversation URL (no navigation)", page.url().includes(`/assistant/c/${sid}`), page.url().replace(BASE, ""));
    record(3, "\"Open full page\" links to the record", (await drawer.getByRole("link", { name: /Open full page/ }).getAttribute("href").catch(() => "")) === href);
    await page.screenshot({ path: path.join(OUT, "3-drawer.png"), fullPage: true });
    await page.keyboard.press("Escape");
    await drawer.waitFor({ state: "detached", timeout: 5000 }).catch(() => {});
    record(3, "Escape closes drawer; conversation intact",
      !(await drawer.isVisible().catch(() => false)) && (await page.locator(".sn-asst-user__bubble", { hasText: "students in 7-A" }).isVisible()));
    await ctx.close();

    // Authorization: the drawer's endpoint re-checks scope on every fetch. Learner roles may
    // read only their own / linked child's record; the other student's record is refused.
    // (The fixture subject teacher teaches 7-A via its timetable slot, so 200 is correct there.)
    for (const [persona, own, other] of [
      ["parent", FX.student_id, FX.student2_id],
      ["student", FX.student_id, FX.student2_id],
    ]) {
      const s = await session(browser, persona);
      const tok = await s.page.evaluate(() => sessionStorage.getItem("sn_access_token"));
      const get = (id) => fetch(`${API}/api/v1/academic/students/${id}/profile`, {
        headers: { "X-Tenant-Slug": FX.tenant_slug, Authorization: `Bearer ${tok}` },
      }).then((r) => r.status);
      const [ownS, otherS] = [await get(own), await get(other)];
      record(3, `${persona}: own/linked record allowed, other student's record denied`,
        ownS === 200 && [403, 404].includes(otherS), `own=${ownS} other=${otherS}`);
      await s.ctx.close();
    }
    {
      const t = await session(browser, "teacher");
      const tok = await t.page.evaluate(() => sessionStorage.getItem("sn_access_token"));
      const st = await fetch(`${API}/api/v1/academic/students/${studentId}/profile`, {
        headers: { "X-Tenant-Slug": "not-" + FX.tenant_slug, Authorization: `Bearer ${tok}` },
      }).then((r) => r.status);
      record(3, "token presented under another tenant is rejected", [400, 401, 403, 404].includes(st), `cross-tenant → ${st}`);
      await t.ctx.close();
    }
  }

  await browser.close();
  fs.writeFileSync(path.join(OUT, "results.json"), JSON.stringify(results, null, 2));
  const failed = results.filter((x) => !x.ok);
  const unexpected = network.filter((n) => n.status >= 500);
  console.log(`\n${results.length - failed.length}/${results.length} checks passed; 5xx=${unexpected.length}; console errors=${errors.length}; evidence: ${OUT}`);
  for (const e of errors.slice(0, 10)) console.log(`  ERR ${e.slice(0, 180)}`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => {
  console.error("HARNESS ERROR:", e);
  process.exit(2);
});
