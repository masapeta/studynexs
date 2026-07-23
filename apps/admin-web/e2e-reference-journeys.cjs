/**
 * Gate 1 — Reference School browser journeys (tenant `reference`).
 * One controlled UI login per persona: principal, teacher, parent, student.
 *
 * Prereqs: API on 127.0.0.1:8000, web built with NEXT_PUBLIC_TENANT_SLUG=reference.
 * Run:  E2E_BASE_URL=http://localhost:3002 node e2e-reference-journeys.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const {
  REFERENCE_TENANT,
  requireReferenceTenant,
  attachConsoleGuard,
  attachTenantTracker,
  reportConsoleErrors,
} = require("./e2e-harness-utils.cjs");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const TENANT = process.env.E2E_TENANT_SLUG || REFERENCE_TENANT;
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-reference-journeys");
const LOGIN_GAP_MS = Number(process.env.E2E_LOGIN_GAP_MS || 15000);

requireReferenceTenant(TENANT);

const PERSONAS = [
  {
    key: "principal",
    portal: "staff",
    homePattern: "**/dashboard**",
    routes: [
      { url: "/dashboard", name: "principal-dashboard", expect: ["Students", "Attendance"] },
      { url: "/dashboard/teaching/curriculum", name: "principal-curriculum", expect: ["Curriculum", "Mathematics"] },
      { url: "/dashboard/teaching/exams", name: "principal-exams", expect: ["Exam"] },
    ],
  },
  {
    key: "teacher",
    portal: "teacher",
    homePattern: "**/teacher**",
    routes: [
      { url: "/dashboard/teaching", name: "teacher-hub", expect: ["Teaching", "Lesson"] },
      { url: "/dashboard/teaching/lesson-plans", name: "teacher-lesson-plans", expect: ["Lesson"] },
      { url: "/dashboard/teaching/ai-papers", name: "teacher-ai-papers", expect: ["Question Paper"] },
      { url: "/dashboard/teaching/exams", name: "teacher-exams", expect: ["Exam"] },
    ],
  },
  {
    key: "parent",
    portal: "parent",
    homePattern: "**/parent**",
    routes: [{ url: "/parent", name: "parent-home", expect: ["Parent", "Child"] }],
  },
  {
    key: "student",
    portal: "student",
    homePattern: "**/student**",
    routes: [
      { url: "/student", name: "student-home", expect: ["Student"] },
      { url: "/student/tutor", name: "student-tutor", expect: ["Tutor", "Fractions", "Mistake"] },
    ],
  },
];

const results = [];
const consoleBuckets = { all: [], disallowed: [] };

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

async function uiLogin(page, persona) {
  await openPasswordLogin(page, persona.portal);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.waitForURL(persona.homePattern, { timeout: 45000 });
}

async function waitForPageReady(page) {
  await page
    .waitForFunction(
      () => {
        const loading = document.querySelector(".loading-screen .spinner");
        return !loading || !loading.offsetParent;
      },
      { timeout: 20000 }
    )
    .catch(() => {});
  await page.waitForTimeout(800);
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true });
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const tenantTracker = attachTenantTracker(page, TENANT);
  attachConsoleGuard(page, consoleBuckets);

  for (let i = 0; i < PERSONAS.length; i++) {
    const persona = PERSONAS[i];
    if (i > 0) {
      await ctx.clearCookies();
      await page.evaluate(() => sessionStorage.clear());
      tenantTracker.reset();
      await sleep(LOGIN_GAP_MS);
    }
    try {
      await uiLogin(page, persona);
      results.push([true, `login ${persona.key}`, page.url()]);
      results.push(tenantTracker.assert(`tenant ${persona.key}`));
      await waitForPageReady(page);
      await shot(page, `${persona.key}-home`);

      for (const route of persona.routes) {
        try {
          await page.goto(BASE + route.url, { waitUntil: "domcontentloaded", timeout: 60000 });
          await waitForPageReady(page);
          const body = await page.locator("body").innerText();
          const ok = route.expect.some((t) => body.includes(t)) && body.length > 100;
          results.push([
            ok,
            `${persona.key}: ${route.name}`,
            ok ? "rendered" : `missing ${JSON.stringify(route.expect)}`,
          ]);
          await shot(page, route.name);
        } catch (e) {
          results.push([false, `${persona.key}: ${route.name}`, e.message]);
          await shot(page, `${route.name}-FAIL`);
        }
      }
    } catch (e) {
      results.push([false, `login ${persona.key}`, e.message]);
      await shot(page, `${persona.key}-login-FAIL`);
    }
  }

  await browser.close();

  console.log("\n" + "=".repeat(72));
  console.log(`Reference School journeys · tenant=${TENANT} · base=${BASE}`);
  let fails = 0;
  for (const [ok, label, note] of results) {
    if (!ok) fails++;
    console.log(`${ok ? "OK  " : "FAIL"}  ${String(label).padEnd(36)} ${note}`);
  }
  console.log("=".repeat(72));
  const disallowedCount = reportConsoleErrors(consoleBuckets);
  if (disallowedCount > 0) fails += 1;
  console.log(
    `${fails === 0 ? "ALL GREEN" : fails + " FAILED"}  (${results.length} checks` +
      `${disallowedCount ? ` + ${disallowedCount} console error(s)` : ", 0 disallowed console errors"})` +
      `  shots: ${SHOTS}`
  );
  process.exit(fails ? 1 : 0);
})();
