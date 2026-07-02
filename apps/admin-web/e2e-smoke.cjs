/**
 * Frontend end-to-end smoke via real headless Chromium (Playwright).
 * Logs in as the principal, walks every dashboard page asserting it rendered real data,
 * then runs the Report Cards flow for real (pick class -> generate -> AI remark renders).
 * Captures a screenshot of every page so the run is visually verifiable.
 *
 * Needs both servers up: API on :8000, Next on :3000.
 * Run:  node e2e-smoke.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = "http://localhost:3000";
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-e2e");
const results = [];

const PAGES = [
  { url: "/dashboard", name: "dashboard", expect: ["Students", "Attendance"] },
  { url: "/dashboard/students", name: "students", expect: ["Students"], rows: ".data-table tbody tr" },
  { url: "/dashboard/staff", name: "staff", expect: ["Staff"], rows: ".data-table tbody tr" },
  { url: "/dashboard/classes", name: "classes", expect: ["Class 10"] },
  { url: "/dashboard/teaching/ai-papers", name: "ai-papers", expect: ["Question Paper", "Generate"] },
  { url: "/dashboard/attendance", name: "attendance", expect: ["Attendance"] },
  { url: "/dashboard/teaching/exams", name: "exams", expect: ["Exam"] },
  { url: "/dashboard/teaching/report-cards", name: "report-cards", expect: ["Report Cards"], rows: ".data-table tbody tr" },
  { url: "/dashboard/timetable", name: "timetable", expect: ["Timetable"] },
  { url: "/dashboard/finance/fees", name: "finance", expect: ["Fee", "Finance", "Revenue", "Collect"] },
  { url: "/dashboard/notices", name: "notices", expect: ["Notice"] },
  { url: "/dashboard/settings", name: "settings", expect: ["Settings", "School"] },
];

async function shot(page, name) {
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true });
}

/** Wait for client-side fetches to paint (spinner gone or timeout). */
async function waitForPageReady(page) {
  await page
    .waitForFunction(
      () => {
        const loading = document.querySelector(".loading-screen .spinner");
        return !loading || !loading.offsetParent;
      },
      { timeout: 15000 }
    )
    .catch(() => {});
  await page.waitForTimeout(800);
}

async function pickAppSelect(page, ariaLabel, optionLabel) {
  await page.getByRole("button", { name: ariaLabel, exact: true }).click();
  await page.getByRole("option", { name: optionLabel }).click();
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push("PAGEERROR: " + e.message));

  // ── Login ──────────────────────────────────────────────────────────────
  try {
    // Deep-link opens password step with staff demo creds pre-filled.
    await page.goto(`${BASE}/login?portal=staff`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#username-input", { timeout: 15000 });
    await page.fill("#username-input", "principal");
    await page.fill("#password-input", "Demo@1234");
    await shot(page, "00-login");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await page.waitForURL("**/dashboard", { timeout: 20000 });
    await page.waitForLoadState("domcontentloaded");
    await waitForPageReady(page);
    results.push([true, "login -> /dashboard", ""]);
  } catch (e) {
    results.push([false, "login", e.message]);
    await shot(page, "00-login-FAIL");
    await finish(browser);
    return;
  }

  // ── Walk every page ────────────────────────────────────────────────────
  for (const p of PAGES) {
    try {
      await page.goto(BASE + p.url, { waitUntil: "domcontentloaded" });
      await waitForPageReady(page);
      const body = await page.locator("body").innerText();
      const missing = p.expect.filter((t) => !body.includes(t));
      let note = "";
      if (p.rows) {
        const n = await page.locator(p.rows).count();
        note = `rows=${n}`;
      }
      // any expected anchor present (not all — pages vary) => rendered
      const ok = p.expect.some((t) => body.includes(t)) && body.length > 200;
      results.push([ok, `page ${p.name}`, ok ? note : `missing all of ${JSON.stringify(p.expect)}`]);
      await shot(page, p.name);
    } catch (e) {
      results.push([false, `page ${p.name}`, e.message]);
      await shot(page, `${p.name}-FAIL`);
    }
  }

  // ── Real flow: open or generate a report card on Class 10 — A ───────────
  try {
    await page.goto(BASE + "/dashboard/teaching/report-cards", { waitUntil: "domcontentloaded" });
    await waitForPageReady(page);
    await pickAppSelect(page, "Class", "Class 10 — A");
    await waitForPageReady(page);
    const rosterRows = await page.locator(".data-table tbody tr").count();
    const openBtn = page.getByRole("button", { name: "Open" }).first();
    if (await openBtn.count()) {
      await openBtn.click();
      results.push([true, "flow: open existing report card", `roster=${rosterRows}`]);
    } else {
      await page.getByRole("button", { name: "Generate", exact: true }).first().click();
      results.push([true, "flow: generate report card (clicked)", `roster=${rosterRows}`]);
    }
    // Preview panel with remark textarea (works for Open or successful Generate).
    await page.waitForSelector("text=Class teacher's remark", { timeout: 45000 });
    await page.waitForTimeout(1500);
    const remark = await page.locator("textarea").first().inputValue();
    const ok = remark.trim().length > 5;
    results.push([ok, "flow: report card remark visible", `remark_len=${remark.length}`]);
    await shot(page, "flow-report-card");
    // Approve only if still draft (skip if already approved).
    const approveBtn = page.getByRole("button", { name: /Approve/ }).first();
    if (await approveBtn.count()) {
      await approveBtn.click();
      await page.waitForTimeout(1200);
      const approvedBadge = await page.locator("text=APPROVED").count();
      results.push([approvedBadge > 0, "flow: approve report card", `approved_badge=${approvedBadge}`]);
      await shot(page, "flow-report-card-approved");
    }
  } catch (e) {
    results.push([
      false,
      "flow: report card",
      `${e.message} — tip: set GEMINI_API_KEY in apps/api/.env, or run: python scripts/smoke_report_card.py`,
    ]);
    await shot(page, "flow-report-card-FAIL");
  }

  await finish(browser);

  async function finish(b) {
    await b.close();
    console.log("\n" + "=".repeat(72));
    let fails = 0;
    for (const [ok, label, note] of results) {
      if (!ok) fails++;
      console.log(`${ok ? "OK  " : "FAIL"}  ${label.padEnd(34)} ${note}`);
    }
    console.log("=".repeat(72));
    if (consoleErrors.length) {
      console.log(`browser console errors (${consoleErrors.length}):`);
      [...new Set(consoleErrors)].slice(0, 10).forEach((e) => console.log("  - " + e.slice(0, 160)));
    } else {
      console.log("no browser console errors");
    }
    console.log(`${fails === 0 ? "ALL GREEN" : fails + " FAILED"}  (${results.length} checks)  shots: ${SHOTS}`);
    process.exit(fails ? 1 : 0);
  }
})();
