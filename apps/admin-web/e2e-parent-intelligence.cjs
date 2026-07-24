/**
 * Focused Parent Intelligence browser proof.
 *
 * Parent path only:
 *   Parent home -> linked child -> learning brief -> why/explainability ->
 *   home support -> grounded Parent Copilot answer.
 *
 * Run:
 *   E2E_BASE_URL=http://127.0.0.1:3002 E2E_API_URL=http://127.0.0.1:8000 node e2e-parent-intelligence.cjs
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
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-parent-intelligence");

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
    const token = await loginViaApi(page, "parent_demo", "Demo@1234");
    const portal = await apiGet(page, token, "/api/v1/portal/context");
    const child = portal.children?.[0];
    const studentId = child?.student_id;
    if (!studentId) throw new Error("parent_demo has no linked child");

    const daily = await apiGet(page, token, `/api/v1/tutor/students/${studentId}/daily-plan`);
    results.push([
      daily.status === "ready" &&
        daily.grounded &&
        !daily.fallback &&
        !!daily.pack_id &&
        !!daily.concept_id,
      "linked child daily plan API",
      `${daily.topic} from ${daily.mastery_topic}`,
    ]);

    const briefing = await apiGet(
      page,
      token,
      `/api/v1/parent-copilot/students/${studentId}/briefing`
    );
    results.push([
      briefing.grounded &&
        !briefing.fallback &&
        briefing.pack_id === daily.pack_id &&
        briefing.concept_id === daily.concept_id &&
        briefing.source_count > 0,
      "briefing same evidence API",
      `${briefing.evidence_reason || ""}`.slice(0, 90),
    ]);

    await installSession(page, token);
    await page.goto(`${BASE}/parent`, { waitUntil: "domcontentloaded", timeout: 60000 });
    let body = await bodyText(page);
    results.push([
      !body.includes("Username & password") && body.includes(child.name),
      "parent home linked child",
      page.url(),
    ]);
    results.push(tenantTracker.assert("tenant parent"));
    await shot(page, "00-parent-home");

    await page.goto(`${BASE}/parent/child/${studentId}`, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    await page.getByTestId("parent-learning-brief").waitFor({ state: "visible", timeout: 90000 });
    await page.getByTestId("parent-evidence-status").waitFor({ state: "visible", timeout: 90000 });
    body = await bodyText(page);
    const normalizedBody = body.toLowerCase();
    results.push([
      normalizedBody.includes("learning briefing") &&
        normalizedBody.includes("why this recommendation") &&
        normalizedBody.includes("evidence verified"),
      "learning brief explains why",
      page.url(),
    ]);
    results.push([
      normalizedBody.includes("how to help at home") && (await page.getByTestId("parent-home-support").count()) > 0,
      "home support guidance",
      "visible tips",
    ]);
    await shot(page, "01-child-learning-brief");

    await page
      .locator("#parent-copilot-question")
      .fill(`How can I help at home with ${daily.topic} tonight?`);
    await page.getByRole("button", { name: "Ask" }).click();
    await page.getByTestId("parent-copilot-answer").waitFor({ state: "visible", timeout: 90000 });
    body = await bodyText(page);
    results.push([
      body.includes("Grounded response") && body.toLowerCase().includes("based on your child"),
      "parent copilot grounded answer",
      "answer displayed",
    ]);
    await shot(page, "02-parent-copilot-answer");
  } catch (e) {
    results.push([false, "parent intelligence walkthrough", e.message]);
    await shot(page, "FAIL");
  } finally {
    await browser.close();
  }

  console.log("\n" + "=".repeat(84));
  console.log(`Parent Intelligence browser proof - tenant=${TENANT} - base=${BASE}`);
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
