/**
 * Phase 0 visual review capture — principal journey.
 * Output: docs/ui-audit/reviews/phase0/
 *
 * Usage:
 *   node scripts/phase0-review-capture.cjs
 *
 * Env: E2E_BASE_URL (default http://127.0.0.1:3000), E2E_API_URL (default http://127.0.0.1:8000)
 *       REVIEW_PHASE (default phase0) — output folder under docs/ui-audit/reviews/
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const BASE = process.env.E2E_BASE_URL || "http://127.0.0.1:3000";
const API = process.env.E2E_API_URL || "http://localhost:8000";
const TENANT = process.env.E2E_TENANT || "test";
const PHASE = (process.env.REVIEW_PHASE || "phase0").replace(/[^a-z0-9.-]/gi, "");
const REPO = path.resolve(__dirname, "../../..");
const OUT = path.join(REPO, "docs/ui-audit/reviews", PHASE);
const BEFORE = path.join(OUT, "before");

async function apiUp() {
  try {
    const res = await fetch(`${API}/health`, { signal: AbortSignal.timeout(8000) });
    return res.ok;
  } catch {
    return false;
  }
}

async function loginViaApi(ctx) {
  const res = await ctx.request.post(`${API}/api/v1/auth/login`, {
    headers: { "Content-Type": "application/json", "X-Tenant-Slug": TENANT },
    data: { username: "principal", password: "Demo@1234" },
  });
  if (!res.ok()) throw new Error(`API login failed (${res.status()})`);
  const body = await res.json();
  const token =
    body.access_token ||
    (body.data && typeof body.data === "object" ? body.data.access_token : null);
  if (!token) throw new Error("API login response missing access_token");
  return token;
}

/** Authenticate and land on dashboard — UI login (API URL must reach Docker on Windows: localhost:8000). */
async function openAuthenticatedDashboard(page) {
  await openPasswordLogin(page);
  await page.locator("#username-input").fill("principal");
  await page.locator("#password-input").fill("Demo@1234");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await page.locator(".sidebar-brand").waitFor({ state: "visible", timeout: 60000 });
  await waitReady(page);
  await page
    .waitForFunction(
      () => {
        const busy = document.querySelector(".briefing-page[aria-busy='true']");
        return !busy;
      },
      { timeout: 45000 }
    )
    .catch(() => {});
  await page.waitForTimeout(2000);
}

async function openPasswordLogin(page) {
  await page.goto(`${BASE}/login?portal=staff`, { waitUntil: "networkidle", timeout: 90000 });
  const username = page.locator("#username-input");
  try {
    await username.waitFor({ state: "visible", timeout: 30000 });
  } catch {
    const onMethod = await page.getByText("Welcome back").isVisible().catch(() => false);
    if (onMethod) await page.getByRole("button", { name: /Username & password/i }).click();
    await username.waitFor({ state: "visible", timeout: 30000 });
  }
}

async function waitReady(page) {
  await page
    .waitForFunction(
      () => {
        const entry = document.querySelector(".sn-entry-loading");
        const spin = document.querySelector(".loading-screen .spinner");
        if (entry && entry.offsetParent) return false;
        if (spin && spin.offsetParent) return false;
        return true;
      },
      { timeout: 45000 }
    )
    .catch(() => {});
  await page.waitForTimeout(1200);
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  fs.mkdirSync(BEFORE, { recursive: true });

  const manifest = {
    capturedAt: new Date().toISOString(),
    phase: PHASE,
    base: BASE,
    apiAvailable: await apiUp(),
    shots: [],
  };

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  async function capture(name, fn, note) {
    try {
      const file = await fn();
      manifest.shots.push({ name, file, ok: true, note });
      console.log("OK ", name);
    } catch (e) {
      manifest.shots.push({ name, ok: false, error: e.message, note });
      console.log("FAIL", name, e.message);
    }
  }

  await capture("01-landing", async () => {
    await page.goto(`${BASE}/products/studynexs`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForTimeout(1500);
    const file = path.join(OUT, "01-landing.png");
    await page.screenshot({ path: file, fullPage: false });
    return file;
  }, "StudyNexs product landing (reference)");

  await capture("02-login", async () => {
    await openPasswordLogin(page);
    await page.waitForTimeout(800);
    const file = path.join(OUT, "02-login.png");
    await page.screenshot({ path: file, fullPage: false });
    return file;
  }, "Staff login — marketing shell bridge");

  await capture("03-loading", async () => {
    await ctx.clearCookies();
    await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded", timeout: 60000 });
    const entry = page.locator(".sn-entry-loading");
    await entry.waitFor({ state: "visible", timeout: 8000 }).catch(() => {});
    const file = path.join(OUT, "03-loading.png");
    if (await entry.isVisible().catch(() => false)) {
      try {
        await entry.screenshot({ path: file });
      } catch {
        await page.screenshot({ path: file, fullPage: false });
      }
    } else {
      await page.screenshot({ path: file, fullPage: false });
    }
    return file;
  }, "AppEntryLoading during auth bootstrap");

  if (manifest.apiAvailable) {
    try {
      await ctx.clearCookies();
      await openAuthenticatedDashboard(page);

      await capture("04-dashboard", async () => {
        const file = path.join(OUT, "04-dashboard.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Principal morning briefing shell");

      await capture("05-sidebar", async () => {
        const sidebar = page.locator(".sidebar-brand, .sidebar").first();
        await sidebar.waitFor({ state: "visible", timeout: 20000 });
        const file = path.join(OUT, "05-sidebar.png");
        await sidebar.screenshot({ path: file });
        return file;
      }, "StudyNexs + school brand hierarchy");

      await capture("06-dashboard-full", async () => {
        const file = path.join(OUT, "06-dashboard-full.png");
        await page.screenshot({ path: file, fullPage: true });
        return file;
      }, "Full-page dashboard — visual regression baseline");
    } catch (e) {
      for (const name of ["04-dashboard", "05-sidebar", "06-dashboard-full"]) {
        manifest.shots.push({ name, ok: false, error: e.message });
        console.log("FAIL", name, e.message);
      }
    }
  } else {
    manifest.shots.push({
      name: "04-dashboard",
      ok: false,
      error: "API unavailable — start infra/docker and re-run",
    });
    manifest.shots.push({
      name: "05-sidebar",
      ok: false,
      error: "API unavailable — start infra/docker and re-run",
    });
    manifest.shots.push({
      name: "06-dashboard-full",
      ok: false,
      error: "API unavailable — start infra/docker and re-run",
    });
    console.log("SKIP 04-dashboard, 05-sidebar, 06-dashboard-full (API down)");
  }

  // Phase 2A: interaction state spot-checks
  if (PHASE === "phase2a") {
    const AFTER = path.join(OUT, "after");
    fs.mkdirSync(AFTER, { recursive: true });

    await capture("spot-01-login-focus", async () => {
      await openPasswordLogin(page);
      await page.locator("#username-input").focus();
      const file = path.join(AFTER, "spot-01-login-focus.png");
      await page.screenshot({ path: file, fullPage: false });
      return file;
    }, "Login form — username focus ring");

    if (manifest.apiAvailable) {
      await capture("spot-02-nav-focus", async () => {
        await ctx.clearCookies();
        await openAuthenticatedDashboard(page);
        const nav = page.locator(".nav-item").first();
        await nav.focus();
        const file = path.join(AFTER, "spot-02-nav-focus.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Sidebar nav — focus-visible ring");

      await capture("spot-03-semantic-states", async () => {
        const html = `<!DOCTYPE html><html><head>
          <link rel="stylesheet" href="${BASE}/_next/static/css/app/layout.css">
          <style>body{margin:0;font-family:Inter,sans-serif;background:#f8fafc;padding:32px;display:grid;gap:16px;max-width:480px}
          .row{padding:14px 16px;border-radius:14px;font-size:14px;font-weight:600}</style></head><body>
          <div class="row platform-state--success">Success — action completed</div>
          <div class="row platform-state--warning">Warning — review required</div>
          <div class="row platform-state--error">Error — something went wrong</div>
          </body></html>`;
        await page.setContent(html, { waitUntil: "domcontentloaded" });
        const file = path.join(AFTER, "spot-03-semantic-states.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Success / warning / error platform states");
    }
  }

  // Phase 2B: accessibility spot-checks
  if (PHASE === "phase2b") {
    const AFTER = path.join(OUT, "after");
    fs.mkdirSync(AFTER, { recursive: true });

    await capture("spot-01-skip-link", async () => {
      await openPasswordLogin(page);
      await page.keyboard.press("Tab");
      const skip = page.locator(".platform-skip-link");
      await skip.waitFor({ state: "visible", timeout: 5000 }).catch(() => {});
      const file = path.join(AFTER, "spot-01-skip-link.png");
      await page.screenshot({ path: file, fullPage: false });
      return file;
    }, "Skip link visible on keyboard focus (login)");

    if (manifest.apiAvailable) {
      await capture("spot-02-nav-focus", async () => {
        await ctx.clearCookies();
        await openAuthenticatedDashboard(page);
        await page.locator(".nav-item").first().focus();
        const file = path.join(AFTER, "spot-02-nav-focus.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Enhanced focus ring on nav item");
    }
  }

  // Phase 2C: component polish spot-checks
  if (PHASE === "phase2c") {
    const AFTER = path.join(OUT, "after");
    fs.mkdirSync(AFTER, { recursive: true });

    await capture("spot-01-login-form", async () => {
      await openPasswordLogin(page);
      await page.locator("#username-input").focus();
      const file = path.join(AFTER, "spot-01-login-form.png");
      await page.screenshot({ path: file, fullPage: false });
      return file;
    }, "Login form — input focus ring");

    if (manifest.apiAvailable) {
      await capture("spot-02-students-table", async () => {
        await ctx.clearCookies();
        await openAuthenticatedDashboard(page);
        await page.goto(`${BASE}/dashboard/students`, { waitUntil: "domcontentloaded", timeout: 60000 });
        await page.waitForTimeout(1500);
        const file = path.join(AFTER, "spot-02-students-table.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Students table — row hover tokens");

      await capture("spot-03-modal", async () => {
        const html = `<!DOCTYPE html><html><head>
          <link rel="stylesheet" href="${BASE}/_next/static/css/app/layout.css">
          <style>body{margin:0;font-family:Inter,sans-serif;background:#f8fafc;padding:24px}
          .wrap{position:relative;height:420px}</style></head><body><div class="wrap">
          <div class="gw-modal-backdrop" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
          <div class="gw-modal sn-app" style="width:min(480px,100%)"><header class="gw-modal-header">
          <h2 class="gw-modal-title">Component preview</h2>
          <button type="button" class="btn btn-ghost gw-modal-close" aria-label="Close">×</button>
          </header><div class="gw-modal-body"><p>Dialog polish via platform-components.css</p></div>
          </div></div></div></body></html>`;
        await page.setContent(html, { waitUntil: "domcontentloaded" });
        const file = path.join(AFTER, "spot-03-modal.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Dialog — token-backed modal chrome");
    }
  }

  // Phase 3A: motion & micro-interaction spot-checks
  if (PHASE === "phase3a") {
    const AFTER = path.join(OUT, "after");
    fs.mkdirSync(AFTER, { recursive: true });

    const baseline2c = path.join(REPO, "docs/ui-audit/reviews/phase2c/06-dashboard-full.png");
    if (fs.existsSync(baseline2c)) {
      fs.copyFileSync(baseline2c, path.join(BEFORE, "06-dashboard-full-phase2c-baseline.png"));
      manifest.baselinePhase2c = path.join(BEFORE, "06-dashboard-full-phase2c-baseline.png");
    }

    await capture("spot-01-modal-enter", async () => {
      const html = `<!DOCTYPE html><html><head>
        <link rel="stylesheet" href="${BASE}/_next/static/css/app/layout.css">
        <style>body{margin:0;font-family:Inter,sans-serif;background:#f8fafc;padding:24px}
        .wrap{position:relative;height:420px}</style></head><body><div class="wrap">
        <div class="gw-modal-backdrop gw-modal-backdrop--enter" style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center">
        <div class="gw-modal sn-app" style="width:min(480px,100%)"><header class="gw-modal-header">
        <h2 class="gw-modal-title">Modal enter motion</h2>
        <button type="button" class="btn btn-ghost gw-modal-close" aria-label="Close">×</button>
        </header><div class="gw-modal-body"><p>Phase 3A — platform-motion.css enter state</p></div>
        </div></div></div></body></html>`;
      await page.setContent(html, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(400);
      const file = path.join(AFTER, "spot-01-modal-enter.png");
      await page.screenshot({ path: file, fullPage: false });
      return file;
    }, "Dialog enter — token-backed modal motion");

    await capture("spot-02-entry-reduced-motion", async () => {
      await page.emulateMedia({ reducedMotion: "reduce" });
      await ctx.clearCookies();
      await page.goto(`${BASE}/dashboard`, { waitUntil: "domcontentloaded", timeout: 60000 });
      const entry = page.locator(".sn-entry-loading");
      await entry.waitFor({ state: "visible", timeout: 8000 }).catch(() => {});
      await page.waitForTimeout(600);
      const file = path.join(AFTER, "spot-02-entry-reduced-motion.png");
      await page.screenshot({ path: file, fullPage: false });
      await page.emulateMedia({ reducedMotion: "no-preference" });
      return file;
    }, "Entry loading — prefers-reduced-motion (static skeleton)");

    if (manifest.apiAvailable) {
      await capture("spot-03-briefing-loaded", async () => {
        await ctx.clearCookies();
        await openAuthenticatedDashboard(page);
        await page.locator(".platform-motion-briefing-enter").waitFor({ state: "visible", timeout: 30000 }).catch(() => {});
        await page.waitForTimeout(800);
        const file = path.join(AFTER, "spot-03-briefing-loaded.png");
        await page.screenshot({ path: file, fullPage: false });
        return file;
      }, "Briefing content — platform-motion-briefing-enter at rest");
    }
  }

  // Phase 3C: CSS maintainability — visual regression vs Phase 3A baseline
  if (PHASE === "phase3c") {
    const baseline3a = path.join(REPO, "docs/ui-audit/reviews/phase3a/06-dashboard-full.png");
    if (fs.existsSync(baseline3a)) {
      fs.copyFileSync(baseline3a, path.join(BEFORE, "06-dashboard-full-phase3a-baseline.png"));
      manifest.baselinePhase3a = path.join(BEFORE, "06-dashboard-full-phase3a-baseline.png");
    }
  }

  // Before states (Phase 0 only)
  if (PHASE === "phase0") {
  await capture("before-03-loading-spinner", async () => {
    const html = `<!DOCTYPE html><html><head>
      <link rel="stylesheet" href="${BASE}/_next/static/css/app/layout.css">
      <style>
        body{margin:0;font-family:Inter,sans-serif;background:#f6f4ee}
        .loading-screen{min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px}
        .spinner{width:40px;height:40px;border:3px solid #e8e3d6;border-top-color:#16233d;border-radius:50%;animation:spin .7s linear infinite}
        @keyframes spin{to{transform:rotate(360deg)}}
        p{color:#94a3b8;font-size:14px}
      </style></head><body>
      <div class="loading-screen"><div class="spinner"></div><p>Loading...</p></div>
      </body></html>`;
    await page.setContent(html, { waitUntil: "domcontentloaded" });
    const file = path.join(BEFORE, "03-loading-before.png");
    await page.screenshot({ path: file, fullPage: false });
    return file;
  }, "Reconstructed pre-Phase-0 spinner (documented in REVIEW.md)");

  await capture("before-05-sidebar-greenwood", async () => {
    const html = `<!DOCTYPE html><html><head><style>
      body{margin:0;font-family:Inter,sans-serif;background:#f8fafc;padding:24px}
      .sidebar{width:240px;background:rgba(255,255,255,.78);border:1px solid rgba(148,163,184,.2);border-radius:16px;padding:0}
      .sidebar-brand{padding:14px;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(148,163,184,.15)}
      .mark{width:36px;height:36px;border-radius:8px;background:#a9772b;color:#fff;font-weight:800;font-size:18px;display:flex;align-items:center;justify-content:center}
      .line{font-size:13px;font-weight:700;color:#0f172a}.muted{font-weight:500;color:#94a3b8;font-size:12px}
    </style></head><body><div class="sidebar"><div class="sidebar-brand">
      <div class="mark">G</div><div><div class="line">Greenwood</div><div class="line muted">Public School</div></div>
    </div></div></body></html>`;
    await page.setContent(html);
    const file = path.join(BEFORE, "05-sidebar-before.png");
    await page.screenshot({ path: file });
    return file;
  }, "Reconstructed pre-Phase-0 Greenwood G mark");
  }

  fs.writeFileSync(path.join(OUT, "capture-manifest.json"), JSON.stringify(manifest, null, 2));
  await browser.close();

  const fails = manifest.shots.filter((s) => s.ok === false).length;
  console.log(`\nReview package → ${OUT} (${manifest.shots.length - fails}/${manifest.shots.length} OK)`);
  process.exit(fails ? 1 : 0);
})();
