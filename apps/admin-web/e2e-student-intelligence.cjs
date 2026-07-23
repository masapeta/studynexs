/**
 * Focused Student Intelligence browser proof.
 *
 * Student path only:
 *   Home daily plan -> Tutor evidence -> grounded lesson -> Student Copilot.
 *
 * Run:
 *   E2E_BASE_URL=http://127.0.0.1:3002 E2E_API_URL=http://127.0.0.1:8000 node e2e-student-intelligence.cjs
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
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-student-intelligence");

requireReferenceTenant(TENANT);

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
    throw new Error(`API login rate limited for ${username}; wait or clear scoped auth keys`);
  }
  if (!resp.ok()) {
    throw new Error(
      `API login failed for ${username}: ${resp.status()} ${(await resp.text()).slice(0, 200)}`
    );
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
        return spinnerGone && body.length > 120;
      },
      { timeout: 30000 }
    )
    .catch(() => {});
  await page.waitForTimeout(500);
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

async function bodyText(page) {
  await waitForPageReady(page);
  return page.locator("body").innerText();
}

async function apiGet(page, token, pathName) {
  const resp = await page.request.get(`${API}${pathName}`, {
    headers: {
      "X-Tenant-Slug": TENANT,
      Authorization: `Bearer ${token}`,
    },
  });
  if (!resp.ok()) {
    throw new Error(`GET ${pathName} failed: ${resp.status()} ${(await resp.text()).slice(0, 180)}`);
  }
  const body = await resp.json();
  return body.data || body;
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 430, height: 920 } });
  const page = await ctx.newPage();
  const consoleBuckets = { all: [], disallowed: [] };
  const tenantTracker = attachTenantTracker(page, TENANT);
  attachConsoleGuard(page, consoleBuckets);
  attachApiFailureTracker(page, consoleBuckets);

  let fails = 0;
  try {
    const token = await loginViaApi(page, "student_demo", "Demo@1234");
    const portal = await apiGet(page, token, "/api/v1/portal/context");
    const studentId = portal.student_id || portal.children?.[0]?.student_id;
    if (!studentId) throw new Error("student_demo has no student_id");
    const plan = await apiGet(page, token, `/api/v1/tutor/students/${studentId}/daily-plan`);
    results.push([
      plan.status === "ready" &&
        plan.grounded &&
        !plan.fallback &&
        !!plan.lesson_key &&
        !!plan.mastery_topic,
      "daily plan API",
      `${plan.topic} from ${plan.mastery_topic} - ${Math.round(plan.mastery_pct || 0)}%`,
    ]);

    await installSession(page, token);
    await page.goto(`${BASE}/student`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.getByTestId("student-daily-plan").waitFor({ state: "visible", timeout: 60000 });
    let body = await bodyText(page);
    let normalizedBody = body.toLowerCase();
    const sourceTopicText = `from ${plan.mastery_topic}`.toLowerCase();
    results.push([
      normalizedBody.includes("study this today") &&
        normalizedBody.includes("evidence verified") &&
        normalizedBody.includes(sourceTopicText),
      "student home daily plan",
      page.url(),
    ]);
    results.push(tenantTracker.assert("tenant student"));
    await shot(page, "00-student-home");

    await page.getByTestId("student-daily-plan").click();
    await page
      .getByTestId("student-intelligence-evidence")
      .waitFor({ state: "visible", timeout: 90000 });
    body = await bodyText(page);
    normalizedBody = body.toLowerCase();
    results.push([
      page.url().includes("/student/tutor") &&
        normalizedBody.includes("daily learning plan") &&
        normalizedBody.includes("evidence verified") &&
        normalizedBody.includes(sourceTopicText),
      "tutor evidence panel",
      page.url(),
    ]);
    await shot(page, "01-tutor-evidence");

    results.push([
      body.includes(plan.topic) && body.includes("Step 1 of"),
      "grounded tutor lesson",
      plan.lesson_key,
    ]);

    await page.getByText("Step 1 of").waitFor({ state: "visible", timeout: 90000 });

    await page.locator("#copilot-question").fill(`Why should I study ${plan.topic} today?`);
    await page.getByRole("button", { name: "Ask" }).click();
    await page.getByText("Grounded answer").waitFor({ state: "visible", timeout: 90000 });
    body = await bodyText(page);
    normalizedBody = body.toLowerCase();
    results.push([
      normalizedBody.includes("grounded answer") && normalizedBody.includes("sources"),
      "student copilot grounded",
      "answer displayed",
    ]);
    await shot(page, "02-copilot-grounded");
  } catch (e) {
    results.push([false, "student intelligence walkthrough", e.message]);
    await shot(page, "FAIL");
  } finally {
    await browser.close();
  }

  console.log("\n" + "=".repeat(84));
  console.log(`Student Intelligence browser proof - tenant=${TENANT} - base=${BASE}`);
  for (const [ok, label, note] of results) {
    if (!ok) fails++;
    console.log(`${ok ? "OK  " : "FAIL"}  ${String(label).padEnd(34)} ${note}`);
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
