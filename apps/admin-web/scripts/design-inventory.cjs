/**
 * Phase 0A — Design inventory baseline screenshots.
 * Captures marketing + authenticated surfaces before/after UI polish.
 *
 * Requires: API on 127.0.0.1:8000, Next on E2E_BASE_URL (default 127.0.0.1:3000).
 * Output: docs/ui-audit/baseline/{pre-phase0|post-phase0}/
 *
 * Usage:
 *   node scripts/design-inventory.cjs
 *   set PHASE=post-phase0 && node scripts/design-inventory.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8000";
const TENANT = process.env.E2E_TENANT || "test";
const PHASE = process.env.PHASE || "pre-phase0";
const REPO = path.resolve(__dirname, "../../..");
const OUT = path.join(REPO, "docs/ui-audit/baseline", PHASE);

const PUBLIC_PAGES = [
  { url: "/products/studynexs", name: "marketing-studynexs-landing", public: true },
  { url: "/login?portal=staff", name: "login-staff", public: true },
  { url: "/login?portal=teacher", name: "login-teacher", public: true },
  { url: "/login?portal=parent", name: "login-parent", public: true },
];

const ADMIN_PAGES = [
  { url: "/dashboard", name: "admin-dashboard" },
  { url: "/dashboard/students", name: "admin-students" },
  { url: "/dashboard/students/admissions", name: "admin-admissions" },
  { url: "/dashboard/staff", name: "admin-staff" },
  { url: "/dashboard/classes", name: "admin-classes" },
  { url: "/dashboard/attendance", name: "admin-attendance" },
  { url: "/dashboard/teaching/exams", name: "admin-exams" },
  { url: "/dashboard/teaching/ai-papers", name: "admin-ai-papers" },
  { url: "/dashboard/teaching/report-cards", name: "admin-reports-report-cards" },
  { url: "/dashboard/timetable", name: "admin-timetable" },
  { url: "/dashboard/library", name: "admin-library" },
  { url: "/dashboard/finance/fees", name: "admin-fees" },
  { url: "/dashboard/notices", name: "admin-notices" },
  { url: "/dashboard/settings", name: "admin-settings" },
];

const PORTAL_PAGES = {
  staff: ADMIN_PAGES,
  teacher: [{ url: "/dashboard", name: "teacher-dashboard" }],
  parent: [
    { url: "/parent", name: "parent-home" },
    { url: "/parent/fees", name: "parent-fees" },
    { url: "/parent/notices", name: "parent-notices" },
  ],
  student: [
    { url: "/student", name: "student-home" },
    { url: "/student/tutor", name: "student-ai-tutor" },
    { url: "/student/mastery", name: "student-mastery" },
  ],
};

const CREDS = {
  staff: { username: "principal", password: "Demo@1234" },
  teacher: { username: "teacher6", password: "Demo@1234" },
  parent: { username: "parent_demo", password: "Demo@1234" },
  student: { username: "student_demo", password: "Demo@1234" },
};

async function waitForPageReady(page) {
  await page
    .waitForFunction(
      () => {
        const spin = document.querySelector(".loading-screen .spinner");
        const entry = document.querySelector(".sn-entry-loading");
        const busy = document.querySelector('[aria-busy="true"]');
        if (spin && spin.offsetParent) return false;
        if (entry && entry.offsetParent) return false;
        if (busy) return false;
        return true;
      },
      { timeout: 30000 }
    )
    .catch(() => {});
  await page.waitForTimeout(900);
}

async function loginViaApi(ctx, username, password) {
  const res = await ctx.request.post(`${API}/api/v1/auth/login`, {
    headers: { "Content-Type": "application/json", "X-Tenant-Slug": TENANT },
    data: { username, password },
  });
  if (!res.ok()) {
    const body = await res.text();
    throw new Error(`API login failed (${res.status()}): ${body.slice(0, 200)}`);
  }
}

async function openPasswordLogin(page, portal) {
  await page.goto(`${BASE}/login?portal=${portal}`, { waitUntil: "domcontentloaded", timeout: 60000 });
  const username = page.locator("#username-input");
  try {
    await username.waitFor({ state: "visible", timeout: 20000 });
  } catch {
    const onMethod = await page.getByText("Welcome back").isVisible().catch(() => false);
    if (onMethod) {
      await page.getByRole("button", { name: /Username & password/i }).click();
    }
    await username.waitFor({ state: "visible", timeout: 15000 });
  }
  if (portal !== "staff") {
    const tab = portal.charAt(0).toUpperCase() + portal.slice(1);
    await page.getByRole("tab", { name: tab }).click();
  }
}

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  return file;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const manifest = { phase: PHASE, capturedAt: new Date().toISOString(), base: BASE, shots: [] };
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  for (const p of PUBLIC_PAGES) {
    try {
      await page.goto(BASE + p.url, { waitUntil: "domcontentloaded", timeout: 60000 });
      await waitForPageReady(page);
      const file = await shot(page, p.name);
      manifest.shots.push({ name: p.name, url: p.url, file, ok: true });
      console.log("OK  ", p.name);
    } catch (e) {
      manifest.shots.push({ name: p.name, url: p.url, ok: false, error: e.message });
      console.log("FAIL", p.name, e.message);
    }
  }

  for (const [portal, pages] of Object.entries(PORTAL_PAGES)) {
    const creds = CREDS[portal];
    try {
      await ctx.clearCookies();
      await loginViaApi(ctx, creds.username, creds.password);
      await openPasswordLogin(page, portal);
      await page.getByRole("button", { name: "Sign in", exact: true }).click();
      await page.waitForTimeout(1500);
      await waitForPageReady(page);
      const loginShot = await shot(page, `${portal}-after-login`);
      manifest.shots.push({ name: `${portal}-after-login`, ok: true, file: loginShot });
      console.log("OK  ", `${portal}-after-login`);
    } catch (e) {
      manifest.shots.push({ name: `${portal}-after-login`, ok: false, error: e.message });
      console.log("FAIL", `${portal}-after-login`, e.message);
      continue;
    }

    for (const p of pages) {
      try {
        await page.goto(BASE + p.url, { waitUntil: "domcontentloaded", timeout: 60000 });
        await waitForPageReady(page);
        const file = await shot(page, p.name);
        manifest.shots.push({ name: p.name, url: p.url, portal, file, ok: true });
        console.log("OK  ", p.name);
      } catch (e) {
        manifest.shots.push({ name: p.name, url: p.url, portal, ok: false, error: e.message });
        console.log("FAIL", p.name, e.message);
      }
    }
  }

  fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2));
  await browser.close();
  const fails = manifest.shots.filter((s) => !s.ok).length;
  console.log(`\nInventory ${PHASE}: ${manifest.shots.length - fails}/${manifest.shots.length} OK → ${OUT}`);
  process.exit(fails ? 1 : 0);
})();
