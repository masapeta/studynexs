/**
 * Focused Principal Intelligence browser proof.
 *
 * Principal path only:
 *   Principal dashboard -> Intervention Center -> top priority -> evidence link
 *   and owner / recommended human intervention visible.
 *
 * Run:
 *   E2E_BASE_URL=http://127.0.0.1:3002 E2E_API_URL=http://127.0.0.1:8000 node e2e-principal-intelligence.cjs
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
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-principal-intelligence");

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
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 980 } });
  const page = await ctx.newPage();
  const consoleBuckets = { all: [], disallowed: [] };
  const tenantTracker = attachTenantTracker(page, TENANT);
  attachConsoleGuard(page, consoleBuckets);
  attachApiFailureTracker(page, consoleBuckets);

  let fails = 0;
  try {
    const token = await loginViaApi(page, "principal", "Demo@1234");
    const summary = await apiGet(page, token, "/api/v1/dashboard/summary");
    const card = summary.principal_interventions?.[0];
    results.push([
      summary.persona === "admin" && !!card,
      "intervention API",
      card ? card.issue : "no card",
    ]);
    if (!card) throw new Error("No Principal Intervention Center card returned by API");
    results.push([
      !!card.issue &&
        !!card.why_it_matters &&
        !!card.owner &&
        !!card.recommended_intervention &&
        card.recommended_intervention.toLowerCase().includes("human") &&
        Array.isArray(card.evidence) &&
        card.evidence.length > 0,
      "card answers five questions",
      card.owner,
    ]);

    const chain = await apiGet(page, token, card.evidence_chain_href);
    results.push([
      chain.tenant_slug === TENANT &&
        chain.grounded &&
        !chain.fallback &&
        chain.curriculum_pack_ids?.length > 0 &&
        chain.question_paper_ids?.length > 0 &&
        chain.approved_evaluation_ids?.length > 0 &&
        !!chain.mastery,
      "lineage evidence chain",
      `${chain.topic_display} / packs=${chain.curriculum_pack_ids?.length || 0}`,
    ]);

    await installSession(page, token);
    await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page
      .getByTestId("principal-intervention-center")
      .waitFor({ state: "visible", timeout: 90000 });
    await page
      .getByTestId("principal-intervention-card")
      .first()
      .waitFor({ state: "visible", timeout: 90000 });
    const body = await bodyText(page);
    const normalized = body.toLowerCase();
    results.push([
      normalized.includes("intervention center") &&
        normalized.includes("recommended human intervention") &&
        normalized.includes("owner:"),
      "intervention center visible",
      page.url(),
    ]);
    results.push(tenantTracker.assert("tenant principal"));
    await shot(page, "00-principal-intervention-center");
  } catch (e) {
    results.push([false, "principal intelligence walkthrough", e.message]);
    await shot(page, "FAIL");
  } finally {
    await browser.close();
  }

  console.log("\n" + "=".repeat(84));
  console.log(`Principal Intelligence browser proof - tenant=${TENANT} - base=${BASE}`);
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
