/**
 * Deeper-flow smoke (companion to e2e-smoke.cjs, which walks every page).
 * Covers the flows that page-walking doesn't:
 *   1. Student profile drill-down  — list row -> /dashboard/students/[id], parent details render
 *   2. Finance receipt view        — open a recent payment's receipt in a new tab
 *   3. Report-card "Not assessed"  — the new block on the report preview (soft: needs a
 *                                    partially-graded student in the data to actually appear)
 *
 * Honest scope note: admin-web has NO fee-payment UI — process_payment is API/parent-side,
 * so there is no "pay" button to click here. This exercises the receipt-view half; the pay
 * path + counter provisioning are covered by the service tests (tests/test_concurrency.py).
 *
 * Needs both servers up: API on :8000, Next on :3000.  Run:  node e2e-flows.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = "http://localhost:3000";
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-e2e-flows");
const results = [];
const ok = (label, note = "") => results.push([true, label, note]);
const bad = (label, note = "") => results.push([false, label, note]);

async function shot(page, name) {
  try { await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true }); } catch {}
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  page.on("pageerror", (e) => consoleErrors.push("PAGEERROR: " + e.message));

  // ── Login ────────────────────────────────────────────────────────────────
  try {
    await page.goto(`${BASE}/login?portal=staff`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#username-input", { timeout: 15000 });
    await page.fill("#username-input", "principal");
    await page.fill("#password-input", "Demo@1234");
    await page.getByRole("button", { name: "Sign in", exact: true }).click();
    await page.waitForURL("**/dashboard", { timeout: 20000 });
    await page.waitForLoadState("domcontentloaded");
    ok("login -> /dashboard");
  } catch (e) {
    bad("login", e.message);
    await shot(page, "00-login-FAIL");
    return finish(browser);
  }

  // ── 1. Student profile drill-down ──────────────────────────────────────────
  try {
    await page.goto(BASE + "/dashboard/students", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".data-table tbody tr", { timeout: 15000 });
    const rows = await page.locator(".data-table tbody tr").count();
    await page.locator(".data-table tbody tr").first().click();   // row onClick -> /students/[id]
    await page.waitForURL("**/dashboard/students/**", { timeout: 15000 });
    await page.waitForTimeout(700); // profile fetch paints
    const body = await page.locator("body").innerText();
    const anchors = ["Personal Details", "Parents / Guardians"];
    const missing = anchors.filter((t) => !body.includes(t));
    await shot(page, "01-student-profile");
    if (missing.length === 0) ok("student profile drill-down", `roster=${rows}, parent details render`);
    else bad("student profile drill-down", `missing ${JSON.stringify(missing)}`);
  } catch (e) {
    bad("student profile drill-down", e.message);
    await shot(page, "01-student-profile-FAIL");
  }

  // ── 2. Finance + receipt view ───────────────────────────────────────────────
  try {
    await page.goto(BASE + "/dashboard/finance/fees", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(700);
    const body = await page.locator("body").innerText();
    if (body.includes("Total Collected")) ok("finance dashboard renders");
    else bad("finance dashboard renders", "no 'Total Collected'");

    const viewBtns = page.getByRole("button", { name: /View Receipt/ });
    const n = await viewBtns.count();
    if (n === 0) {
      ok("receipt view (skipped)", "no recent payments in demo data");
    } else {
      const [popup] = await Promise.all([
        ctx.waitForEvent("page"),
        viewBtns.first().click(),
      ]);
      await popup.waitForLoadState("domcontentloaded");
      await popup.waitForTimeout(500);
      const rtext = await popup.locator("body").innerText();
      await popup.screenshot({ path: path.join(SHOTS, "02-receipt.png"), fullPage: true }).catch(() => {});
      // The receipt renders the school name + a "Receipt" heading / number.
      const looksLikeReceipt = /receipt/i.test(rtext) && rtext.length > 100;
      if (looksLikeReceipt) ok("receipt opens", `len=${rtext.length}`);
      else bad("receipt opens", `unexpected receipt content (len=${rtext.length})`);
      await popup.close();
    }
    await shot(page, "02-finance");
  } catch (e) {
    bad("finance / receipt", e.message);
    await shot(page, "02-finance-FAIL");
  }

  // ── 3. Report-card "Not assessed" block ─────────────────────────────────────
  // Prefer opening an existing report (no LLM cost); generate only if none exist.
  try {
    await page.goto(BASE + "/dashboard/teaching/report-cards", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    const openBtn = page.getByRole("button", { name: "Open", exact: true });
    let opened = false;
    if (await openBtn.count() > 0) {
      await openBtn.first().click();
      opened = true;
    } else {
      const genBtn = page.getByRole("button", { name: "Generate", exact: true });
      if (await genBtn.count() > 0) {
        await genBtn.first().click();
        await page.waitForSelector("text=Class teacher's remark", { timeout: 45000 });
        opened = true;
      }
    }
    if (!opened) {
      bad("report-card preview", "no student to open/generate (empty class?)");
    } else {
      await page.waitForTimeout(1000);
      const body = await page.locator("body").innerText();
      const previewOk = body.includes("Class teacher") || body.includes("Percentage");
      if (previewOk) ok("report-card preview renders");
      else bad("report-card preview renders", "no preview anchors");
      // The new block: present only when the student has an examined-but-ungraded subject.
      const naCount = await page.locator("text=Not assessed this term:").count();
      ok("report-card 'Not assessed' block",
         naCount > 0 ? "rendered (partially-graded student)" : "absent (all subjects graded) — OK");
      await shot(page, "03-report-card");
    }
  } catch (e) {
    bad("report-card flow", e.message);
    await shot(page, "03-report-card-FAIL");
  }

  return finish(browser);

  async function finish(b) {
    await b.close();
    console.log("\n" + "=".repeat(72));
    let fails = 0;
    for (const [good, label, note] of results) {
      if (!good) fails++;
      console.log(`${good ? "OK  " : "FAIL"}  ${label.padEnd(36)} ${note}`);
    }
    console.log("=".repeat(72));
    if (consoleErrors.length) {
      console.log(`browser console errors (${consoleErrors.length}):`);
      [...new Set(consoleErrors)].slice(0, 8).forEach((e) => console.log("  - " + e.slice(0, 160)));
    } else {
      console.log("no browser console errors");
    }
    console.log(`${fails === 0 ? "ALL GREEN" : fails + " FAILED"}  (${results.length} checks)  shots: ${SHOTS}`);
    process.exit(fails ? 1 : 0);
  }
})();
