/**
 * Focused Learning Intelligence browser proof.
 *
 * Teacher path only:
 *   Gradebook -> Topic Mastery -> Evidence chain -> Practice paper deep link
 *
 * Run:
 *   E2E_BASE_URL=http://127.0.0.1:3002 E2E_API_URL=http://127.0.0.1:8000 node e2e-learning-intelligence.cjs
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
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-learning-intelligence");

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
        return spinnerGone && body.length > 180;
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

async function findVerifiedFlagViaApi(page, token) {
  for (const [status, tab] of [
    ["pending_review", "Pending review"],
    ["approved", "Approved"],
    ["notified", "Sent"],
  ]) {
    const flags = await apiGet(page, token, `/api/v1/mastery/flags?status=${status}`);
    for (const flag of flags || []) {
      const chain = await apiGet(page, token, `/api/v1/mastery/flags/${flag.id}/evidence-chain`);
      if (chain.grounded && !chain.fallback && chain.curriculum_pack_ids?.length) {
        return { flag, chain, tab };
      }
    }
  }
  throw new Error("No runtime-verified mastery flag found for browser proof");
}

async function openFlagEvidenceInUi(page, target) {
  const tabButton = page.getByRole("button", { name: target.tab });
  if (await tabButton.count()) {
    await tabButton.click();
    await waitForPageReady(page);
  }
  const card = page
    .locator(".card")
    .filter({ hasText: target.flag.topic_display })
    .filter({ hasText: target.flag.student_name || target.flag.evidence?.student_name || "" })
    .first();
  await card.getByRole("button", { name: /View evidence chain|Evidence chain loaded/i }).click();
  await card.getByTestId("learning-evidence-chain").waitFor({ state: "visible", timeout: 20000 });
  return target.tab;
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleBuckets = { all: [], disallowed: [] };
  const tenantTracker = attachTenantTracker(page, TENANT);
  attachConsoleGuard(page, consoleBuckets);
  attachApiFailureTracker(page, consoleBuckets);

  let fails = 0;
  try {
    const token = await loginViaApi(page, "teacher6", "Demo@1234");
    const verifiedFlag = await findVerifiedFlagViaApi(page, token);
    await installSession(page, token);
    await page.goto(`${BASE}/teacher`, { waitUntil: "domcontentloaded", timeout: 60000 });
    let body = await bodyText(page);
    results.push([!body.includes("Username & password"), "login teacher", page.url()]);
    results.push(tenantTracker.assert("tenant teacher"));
    await shot(page, "00-teacher-home");

    await page.goto(`${BASE}/dashboard/teaching/gradebook`, { waitUntil: "domcontentloaded", timeout: 60000 });
    body = await bodyText(page);
    results.push([body.includes("Gradebook") || body.includes("Exam"), "gradebook renders", "teacher can open gradebook"]);
    await shot(page, "01-gradebook");

    await page.goto(`${BASE}/dashboard/teaching/mastery`, { waitUntil: "domcontentloaded", timeout: 60000 });
    body = await bodyText(page);
    results.push([body.includes("Topic Mastery") && body.includes("Weakness Flags"), "mastery renders", "teacher can open weak flags"]);
    const sourceTab = await openFlagEvidenceInUi(page, verifiedFlag);
    body = await bodyText(page);
    const normalizedBody = body.toLowerCase();
    const chainOk =
      normalizedBody.includes("learning evidence chain") &&
      normalizedBody.includes("pack:") &&
      normalizedBody.includes("paper:") &&
      normalizedBody.includes("grounded: yes");
    results.push([chainOk, "evidence chain visible", `source tab=${sourceTab}`]);
    await shot(page, "02-mastery-evidence-chain");

    const practice = page.getByRole("button", { name: "Practice paper" }).first();
    if (await practice.count()) {
      await practice.click();
      await waitForPageReady(page);
      body = await bodyText(page);
      results.push([
        page.url().includes("/dashboard/teaching/ai-papers") && body.includes("Question Paper"),
        "practice paper deep link",
        page.url(),
      ]);
      await shot(page, "03-practice-paper-deeplink");
    } else {
      results.push([false, "practice paper deep link", "no Practice paper button"]);
    }
  } catch (e) {
    results.push([false, "learning walkthrough", e.message]);
    await shot(page, "FAIL");
  } finally {
    await browser.close();
  }

  console.log("\n" + "=".repeat(84));
  console.log(`Learning Intelligence browser proof · tenant=${TENANT} · base=${BASE}`);
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
