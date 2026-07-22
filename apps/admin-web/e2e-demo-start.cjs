/**
 * Stage 2B — /demo/start provisions a tenant and lands on curriculum onboarding.
 *
 * Prereqs: API on 127.0.0.1:8000 with demo provisioning enabled, web on E2E_BASE_URL.
 * For production-mode web: `npm run build && npx next start -p 3000` in apps/admin-web.
 *
 * Run: E2E_BASE_URL=http://127.0.0.1:3000 node e2e-demo-start.cjs
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { attachConsoleGuard, reportConsoleErrors } = require("./e2e-harness-utils.cjs");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const API = process.env.E2E_API_URL || "http://127.0.0.1:8000";
const SHOTS = path.join(process.env.TEMP || "/tmp", "sn-demo-start");
const TURNSTILE_SITE_KEY = (process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || "").trim();

const results = [];
const ok = (label, note = "") => results.push([true, label, note]);
const bad = (label, note = "") => results.push([false, label, note]);

async function main() {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const consoleBuckets = { all: [], disallowed: [] };
  const context = await browser.newContext();
  const page = await context.newPage();
  attachConsoleGuard(page, consoleBuckets);

  const observedSlugs = [];
  page.on("request", (req) => {
    if (!req.url().includes("/api/v1/")) return;
    const slug = req.headers()["x-tenant-slug"];
    if (slug) observedSlugs.push(slug);
  });

  let prospectSlug = null;
  let accessToken = null;

  try {
    await page.goto(`${BASE}/demo/start`, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: /start my demo/i }).waitFor({ timeout: 20000 });

    if (TURNSTILE_SITE_KEY) {
      const widget = page.locator(
        '[data-testid="demo-turnstile"] .cf-turnstile, iframe[src*="challenges.cloudflare.com"]'
      );
      const count = await widget.count();
      if (count > 0) ok("turnstile", "widget rendered");
      else bad("turnstile", "site key set but widget not detected");
    } else {
      const stray = await page.locator(
        '.cf-turnstile, iframe[src*="challenges.cloudflare.com"]'
      ).count();
      if (stray > 0) bad("turnstile", "widget visible without site key in env");
      else ok("turnstile", "skipped (no NEXT_PUBLIC_TURNSTILE_SITE_KEY)");
    }

    await page.getByRole("button", { name: /start my demo/i }).click();
    await page.waitForURL("**/dashboard/teaching/curriculum/onboarding**", { timeout: 60000 });
    ok("navigation", "reached curriculum onboarding");

    accessToken = await page.evaluate(() => sessionStorage.getItem("sn_access_token"));
    if (accessToken) ok("access token", "stored in sessionStorage");
    else bad("access token", "missing after demo start");

    prospectSlug = await page.evaluate(() =>
      sessionStorage.getItem("sn_prospect_tenant_slug")
    );
    if (prospectSlug && prospectSlug.startsWith("demo-")) {
      ok("prospect slug", prospectSlug);
    } else {
      bad("prospect slug", `expected demo-* slug, got ${prospectSlug}`);
    }

    const sessionToken = await page.evaluate(() =>
      sessionStorage.getItem("sn_demo_session_token")
    );
    if (sessionToken && sessionToken.length >= 16) ok("session token", "stored for renew");
    else bad("session token", "missing demo session token");

    const cookies = await context.cookies();
    const refreshCookie = cookies.find((c) => c.name === "studynexs_refresh");
    if (refreshCookie) ok("refresh cookie", `path=${refreshCookie.path}`);
    else bad("refresh cookie", "studynexs_refresh not set after demo start");

    const uniqueSlugs = [...new Set(observedSlugs.filter((s) => s.startsWith("demo-")))];
    if (uniqueSlugs.length >= 1 && prospectSlug && uniqueSlugs.includes(prospectSlug)) {
      ok("tenant header", `${prospectSlug} on ${observedSlugs.length} API call(s)`);
    } else {
      bad("tenant header", `expected ${prospectSlug}, saw ${uniqueSlugs.join(", ") || "none"}`);
    }

    if (accessToken && prospectSlug) {
      const me = await fetch(`${API}/api/v1/users/me`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Tenant-Slug": prospectSlug,
        },
      });
      if (me.ok) {
        const body = await me.json();
        ok("/users/me", `role ${body.data?.role || body.role || "unknown"}`);
      } else {
        bad("/users/me", `status ${me.status}`);
      }

      const perms = await fetch(`${API}/api/v1/users/me/permissions`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "X-Tenant-Slug": prospectSlug,
        },
      });
      if (perms.ok) {
        const pdata = (await perms.json()).data || {};
        const flags = Object.entries(pdata).filter(([, v]) => v === true).length;
        ok("permissions", `${flags} capability flags hydrated`);
      } else {
        bad("permissions", `status ${perms.status}`);
      }
    }

    if (refreshCookie) {
      const refreshResult = await page.evaluate(async (apiUrl) => {
        const res = await fetch(`${apiUrl}/api/v1/auth/refresh`, {
          method: "POST",
          credentials: "include",
        });
        const body = await res.json().catch(() => ({}));
        return { ok: res.ok, status: res.status, hasToken: Boolean(body.access_token) };
      }, API);
      if (refreshResult.ok && refreshResult.hasToken) {
        ok("cookie refresh", "POST /auth/refresh returned access_token");
      } else {
        bad("cookie refresh", `status ${refreshResult.status}`);
      }
    }

    await page.screenshot({ path: path.join(SHOTS, "onboarding.png"), fullPage: true });
  } catch (err) {
    bad("demo start flow", err.message);
    await page.screenshot({ path: path.join(SHOTS, "failure.png"), fullPage: true });
  } finally {
    await browser.close();
  }

  reportConsoleErrors(consoleBuckets);
  console.log("\n--- Stage 2B demo start E2E ---");
  let failed = 0;
  for (const [pass, label, note] of results) {
    console.log(`${pass ? "PASS" : "FAIL"}  ${label}${note ? ` — ${note}` : ""}`);
    if (!pass) failed += 1;
  }
  process.exit(failed ? 1 : 0);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
