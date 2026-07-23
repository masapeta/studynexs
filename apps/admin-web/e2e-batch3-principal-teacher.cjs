/**
 * Batch 3 browser walkthrough: Principal + Teacher pilot journeys only.
 *
 * Reuses the existing auth/session/tenant harness and deliberately avoids
 * student/parent Release 0.4 journeys.
 *
 * Run:
 *   E2E_BASE_URL=http://127.0.0.1:3002 E2E_API_URL=http://127.0.0.1:8000 node e2e-batch3-principal-teacher.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const {
  REFERENCE_TENANT,
  requireReferenceTenant,
  attachConsoleGuard,
  attachApiFailureTracker,
  attachTenantTracker,
  reportConsoleErrors,
} = require("./e2e-harness-utils.cjs");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3002";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8000";
const TENANT =
  process.env.E2E_TENANT_SLUG || process.env.NEXT_PUBLIC_TENANT_SLUG || REFERENCE_TENANT;
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-batch3-principal-teacher");

requireReferenceTenant(TENANT);

const PERSONAS = [
  {
    key: "principal",
    username: "principal",
    password: "Demo@1234",
    home: "/dashboard",
    routes: [
      { url: "/dashboard", name: "principal-dashboard", expect: ["Students", "Attendance"] },
      { url: "/dashboard/teaching/curriculum", name: "principal-curriculum", expect: ["Curriculum"] },
      { url: "/dashboard/teaching/lesson-plans", name: "principal-lesson-plans", expect: ["Lesson"] },
      { url: "/dashboard/teaching/ai-papers", name: "principal-question-papers", expect: ["Question Paper"] },
    ],
  },
  {
    key: "teacher",
    username: "teacher6",
    password: "Demo@1234",
    home: "/teacher",
    routes: [
      { url: "/teacher", name: "teacher-home", expect: ["Teaching", "Lesson", "Kiran"] },
      { url: "/dashboard/teaching", name: "teacher-hub", expect: ["Teaching", "Lesson"] },
      { url: "/dashboard/teaching/lesson-plans", name: "teacher-lesson-plans", expect: ["Lesson"] },
      { url: "/dashboard/teaching/ai-papers", name: "teacher-question-papers", expect: ["Question Paper"] },
      { url: "/dashboard/teaching/exams", name: "teacher-exams", expect: ["Exam"] },
    ],
  },
];

const results = [];

async function loginViaApi(page, username, password) {
  const resp = await page.request.post(`${API}/api/v1/auth/login`, {
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-Slug": TENANT,
    },
    data: { username, password },
  });
  if (resp.status() === 429) {
    throw new Error(
      `API login rate limited for ${username}; wait or clear scoped auth:ratelimit keys`
    );
  }
  if (!resp.ok()) {
    throw new Error(`API login failed for ${username}: ${resp.status()} ${(await resp.text()).slice(0, 200)}`);
  }
  const body = await resp.json();
  return body.access_token || body.data?.access_token;
}

async function installSession(page, accessToken) {
  await page.context().addInitScript(
    ({ token, tenant }) => {
      sessionStorage.setItem("sn_access_token", token);
      sessionStorage.setItem("sn_prospect_tenant_slug", tenant);
    },
    { token: accessToken, tenant: TENANT }
  );
}

async function waitForPageReady(page) {
  await page
    .waitForFunction(
      () => {
        const loading = document.querySelector(".loading-screen .spinner");
        const spinnerGone = !loading || !loading.offsetParent;
        const body = document.body?.innerText || "";
        return spinnerGone && body.length > 150;
      },
      { timeout: 25000 }
    )
    .catch(() => {});
  await page.waitForTimeout(400);
}

async function shot(page, name) {
  try {
    await page.screenshot({
      path: path.join(SHOTS, `${name}.png`),
      fullPage: true,
      timeout: 10000,
    });
  } catch (e) {
    console.log(`WARN screenshot skipped for ${name}: ${e.message}`);
  }
}

async function assertRoute(page, persona, route) {
  await page.goto(BASE + route.url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await waitForPageReady(page);
  const body = await page.locator("body").innerText();
  const loginScreen = body.includes("Welcome back") && body.includes("Username & password");
  const matched = route.expect.some((text) => body.includes(text));
  const ok = !loginScreen && matched && body.length > 150;
  results.push([
    ok,
    `${persona.key}: ${route.name}`,
    ok ? "rendered" : `missing ${JSON.stringify(route.expect)} loginScreen=${loginScreen}`,
  ]);
  await shot(page, route.name);
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const consoleBuckets = { all: [], disallowed: [] };

  for (const persona of PERSONAS) {
    const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    const tenantTracker = attachTenantTracker(page, TENANT);
    attachConsoleGuard(page, consoleBuckets);
    attachApiFailureTracker(page, consoleBuckets);

    try {
      const token = await loginViaApi(page, persona.username, persona.password);
      if (!token) throw new Error("login returned no token");
      await installSession(page, token);
      await page.goto(BASE + persona.home, { waitUntil: "domcontentloaded", timeout: 60000 });
      await waitForPageReady(page);
      const body = await page.locator("body").innerText();
      const ok = body.length > 150 && !body.includes("Username & password");
      results.push([ok, `login ${persona.key}`, page.url()]);
      results.push(tenantTracker.assert(`tenant ${persona.key}`));
      await shot(page, `${persona.key}-home`);
      for (const route of persona.routes) {
        await assertRoute(page, persona, route);
      }
    } catch (e) {
      results.push([false, `login/walk ${persona.key}`, e.message]);
      await shot(page, `${persona.key}-FAIL`);
    } finally {
      await ctx.close();
    }
  }

  await browser.close();

  console.log("\n" + "=".repeat(84));
  console.log(`Batch 3 Principal + Teacher browser walkthrough · tenant=${TENANT} · base=${BASE}`);
  let fails = 0;
  for (const [ok, label, note] of results) {
    if (!ok) fails++;
    console.log(`${ok ? "OK  " : "FAIL"}  ${String(label).padEnd(40)} ${note}`);
  }
  console.log("=".repeat(84));
  const disallowedCount = reportConsoleErrors(consoleBuckets);
  if (disallowedCount > 0) fails += 1;
  console.log(
    `${fails === 0 ? "ALL GREEN" : fails + " FAILED"}  (${results.length} checks` +
      `${disallowedCount ? ` + ${disallowedCount} console/API error(s)` : ", 0 disallowed console/API errors"})` +
      `  shots: ${SHOTS}`
  );
  process.exit(fails ? 1 : 0);
})();
