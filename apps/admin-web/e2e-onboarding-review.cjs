/**
 * Stage 2A — onboarding review panel must load pack detail once (no fetch loop).
 *
 * Prereqs: API on 127.0.0.1:8000, production web on E2E_BASE_URL (default :3000),
 * reference tenant, seeded draft pack for principal.
 *
 * Run: E2E_BASE_URL=http://127.0.0.1:3000 node e2e-onboarding-review.cjs
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

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const TENANT = process.env.E2E_TENANT_SLUG || REFERENCE_TENANT;
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-onboarding-review");
const API = process.env.E2E_API_URL || "http://127.0.0.1:8000";

requireReferenceTenant(TENANT);

const results = [];
const ok = (label, note = "") => results.push([true, label, note]);
const bad = (label, note = "") => results.push([false, label, note]);

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

async function authenticateStaff(page) {
  const loginResp = await page.request.post(`${API}/api/v1/auth/login`, {
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-Slug": TENANT,
    },
    data: { username: "principal", password: "Demo@1234" },
  });
  if (loginResp.status() === 429) {
    throw new Error(
      "API login rate limited (429) — wait 15 min or clear auth:ratelimit:login:* in Redis"
    );
  }
  if (!loginResp.ok()) {
    throw new Error(`API login failed: ${loginResp.status()}`);
  }
  const { access_token: accessToken } = await loginResp.json();
  await page.addInitScript(({ token, tenant }) => {
    sessionStorage.setItem("sn_access_token", token);
    sessionStorage.setItem("sn_prospect_tenant_slug", tenant);
  }, { token: accessToken, tenant: TENANT });
  await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded" });
  await page.waitForURL("**/dashboard**", { timeout: 20000 });
  await page.getByText("Students").first().waitFor({ timeout: 15000 });
  return accessToken;
}

async function apiJson(path, token, options = {}) {
  const resp = await fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Tenant-Slug": TENANT,
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  const body = await resp.json().catch(() => ({}));
  return { resp, body };
}

async function ensureDraftPackId(token) {
  const classes = await apiJson("/api/v1/academic/classes?page_size=5", token);
  const classId = classes.body.items?.[0]?.id || classes.body.data?.[0]?.id;
  if (!classId) return null;

  const subjects = await apiJson(`/api/v1/academic/subjects?class_id=${classId}`, token);
  const subjectId = subjects.body.items?.[0]?.id || subjects.body.data?.[0]?.id;
  if (!subjectId) return null;

  const years = await apiJson("/api/v1/school/academic-years", token);
  const yearId = years.body.data?.[0]?.id;
  if (!yearId) return null;

  const created = await apiJson("/api/v1/curriculum/packs", token, {
    method: "POST",
    body: JSON.stringify({
      class_id: classId,
      subject_id: subjectId,
      academic_year_id: yearId,
      board: "SSC",
      book_title: `E2E draft pack ${Date.now()}`,
    }),
  });
  if (!created.resp.ok) return null;
  const packId = created.body.data?.id;
  if (!packId) return null;

  await apiJson(`/api/v1/curriculum/packs/${packId}/chapters`, token, {
    method: "POST",
    body: JSON.stringify({
      title: "E2E Review Chapter",
      topics: [{ title: "E2E Topic", concepts: ["concept-a"] }],
    }),
  });

  return packId;
}

function isExpectedPackDetailRequest(url, packId) {
  try {
    const pathname = new URL(url).pathname;
    return pathname === `/api/v1/curriculum/packs/${packId}`;
  } catch {
    return false;
  }
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  const consoleBuckets = { all: [], disallowed: [] };
  const tenantTracker = attachTenantTracker(page, TENANT);
  attachConsoleGuard(page, consoleBuckets);
  attachApiFailureTracker(page, consoleBuckets);

  let expectedPackId = null;
  const packDetailRequests = [];
  page.on("request", (req) => {
    if (req.method() !== "GET") return;
    if (!expectedPackId) return;
    if (isExpectedPackDetailRequest(req.url(), expectedPackId)) {
      packDetailRequests.push(req.url());
    }
  });

  try {
    const token = await authenticateStaff(page);
    ok("login");
    results.push(tenantTracker.assert("tenant reference"));

    let packId = process.env.E2E_DRAFT_PACK_ID || null;
    if (!packId && token) {
      packId = await ensureDraftPackId(token);
    }

    if (!packId) {
      bad("draft pack lookup", "no draft pack found — seed reference school or set E2E_DRAFT_PACK_ID");
    } else {
      expectedPackId = packId;
      const reviewUrl = `${BASE}/dashboard/teaching/curriculum/onboarding?pack_id=${packId}&step=3`;
      packDetailRequests.length = 0;
      await page.goto(reviewUrl, { waitUntil: "domcontentloaded" });
      await page.getByText("Review and approve").waitFor({ timeout: 20000 });
      await page.getByText(/chapter\(s\), \d+ topic\(s\)/).waitFor({ timeout: 15000 });
      await page.waitForTimeout(1500);
      const count = packDetailRequests.length;
      if (count === 1) {
        ok("single pack detail fetch", `exactly 1 GET /packs/${packId} after review panel load`);
      } else {
        bad(
          "single pack detail fetch",
          `expected exactly 1 GET /packs/${packId}, saw ${count}` +
            (count > 1 ? ` (${packDetailRequests.join(", ")})` : "")
        );
      }
      if (consoleBuckets.disallowed.length === 0) {
        ok("no disallowed console errors");
      } else {
        bad("console errors", consoleBuckets.disallowed.slice(0, 3).join(" | "));
      }
      await shot(page, "onboarding-review");
    }
  } catch (e) {
    bad("onboarding review harness", e.message);
    try {
      await shot(page, "onboarding-review-FAIL");
    } catch {}
  }

  await browser.close();
  reportConsoleErrors(consoleBuckets);

  console.log("\n--- e2e-onboarding-review ---");
  let failed = 0;
  for (const [pass, label, note] of results) {
    console.log(`${pass ? "PASS" : "FAIL"}  ${label}${note ? ` — ${note}` : ""}`);
    if (!pass) failed += 1;
  }
  process.exit(failed ? 1 : 0);
})();
