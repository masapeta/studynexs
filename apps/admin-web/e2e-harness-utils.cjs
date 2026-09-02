/** Shared helpers for Gate 1 browser validation harnesses. */

const REFERENCE_TENANT = "reference";

function requireReferenceTenant(tenant) {
  if (tenant !== REFERENCE_TENANT) {
    throw new Error(
      `Expected E2E_TENANT_SLUG=${REFERENCE_TENANT}, got "${tenant}". ` +
        "Rebuild admin-web with NEXT_PUBLIC_TENANT_SLUG=reference."
    );
  }
}

/** Only the pre-auth refresh 401 is tolerated; CORS and other errors fail the run. */
function isAllowedConsoleError(message) {
  const msg = message.toLowerCase();
  if (msg.includes("cors")) return false;
  if (msg.includes("access-control-allow-origin")) return false;
  if (msg.includes("net::err_failed")) return false;
  if (msg.includes("/api/v1/auth/refresh")) return true;
  if (msg.includes("401") && msg.includes("refresh")) return true;
  // UI login pages can emit a benign pre-auth 401 while probing session state.
  if (
    msg.includes("401") &&
    msg.includes("unauthorized") &&
    msg.includes("/login?portal=") &&
    !msg.includes("/api/v1/")
  ) {
    return true;
  }
  // Chrome omits the URL on the generic pre-auth refresh failure before login.
  if (
    msg.includes("401") &&
    msg.includes("unauthorized") &&
    !msg.includes("/api/v1/") &&
    !msg.includes("login")
  ) {
    return true;
  }
  return false;
}

function attachConsoleGuard(page, buckets) {
  page.on("console", (m) => {
    if (m.type() !== "error") return;
    const text = `${m.text()} [url=${page.url()}]`;
    buckets.all.push(text);
    if (!isAllowedConsoleError(text)) buckets.disallowed.push(text);
  });
  page.on("pageerror", (e) => {
    const text = `PAGEERROR: ${e.message} [url=${page.url()}]`;
    buckets.all.push(text);
    buckets.disallowed.push(text);
  });
}

function attachTenantTracker(page, expectedTenant = REFERENCE_TENANT) {
  const observed = [];
  page.on("request", (req) => {
    if (!req.url().includes("/api/v1/")) return;
    const slug = req.headers()["x-tenant-slug"];
    if (slug) observed.push(slug);
  });
  return {
    observed,
    assert(label = "tenant X-Tenant-Slug") {
      if (observed.length === 0) {
        return [false, label, "no /api/v1 requests carried X-Tenant-Slug"];
      }
      const unique = [...new Set(observed)];
      const unexpected = unique.filter((s) => s !== expectedTenant);
      if (unexpected.length) {
        return [false, label, `saw ${unexpected.join(", ")} (expected ${expectedTenant})`];
      }
      return [true, label, `${expectedTenant} on ${observed.length} API call(s)`];
    },
    reset() {
      observed.length = 0;
    },
  };
}

function isAllowedApiFailure(url, status) {
  if (status === 401 && url.includes("/api/v1/auth/refresh")) return true;
  return false;
}

function attachApiFailureTracker(page, buckets) {
  buckets.apiFailures = buckets.apiFailures || [];
  page.on("response", (res) => {
    const url = res.url();
    const status = res.status();
    if (!url.includes("/api/v1/") || status < 400) return;
    if (isAllowedApiFailure(url, status)) return;
    buckets.apiFailures.push(`${status} ${url} [page=${page.url()}]`);
  });
}

function reportConsoleErrors(buckets) {
  const unique = [...new Set(buckets.all)];
  const disallowed = [...new Set(buckets.disallowed)];
  const apiFailures = [...new Set(buckets.apiFailures || [])];
  if (unique.length) {
    console.log(`browser console errors (${unique.length} total, ${disallowed.length} disallowed):`);
    unique.slice(0, 12).forEach((e) => {
      const tag = isAllowedConsoleError(e) ? "allow" : "FAIL";
      console.log(`  [${tag}] ${e.slice(0, 260)}`);
    });
    if (disallowed.length) {
      console.log("disallowed console details:");
      disallowed.slice(0, 12).forEach((e) => console.log(`  - ${e.slice(0, 320)}`));
    }
  } else {
    console.log("no browser console errors");
  }
  if (apiFailures.length) {
    console.log(`failed API responses (${apiFailures.length}):`);
    apiFailures.slice(0, 12).forEach((e) => console.log(`  - ${e}`));
  }
  return disallowed.length + apiFailures.length;
}

module.exports = {
  REFERENCE_TENANT,
  requireReferenceTenant,
  isAllowedConsoleError,
  attachConsoleGuard,
  attachApiFailureTracker,
  attachTenantTracker,
  reportConsoleErrors,
};
