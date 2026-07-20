/** Tenant slug resolution — shared between API client and demo-mode checks. */

/** Platform hosts — never school tenants. Must match API TENANT_RESERVED_SUBDOMAINS. */
const RESERVED_SUBDOMAINS = new Set([
  "api",
  "app",
  "demo",
  "dev",
  "test",
  "admin",
  "www",
]);

/**
 * Resolve the school tenant slug for API calls.
 *
 * 1. Runtime: {school}.studynexs.com → school (when NEXT_PUBLIC_TENANT_BASE_DOMAIN is set)
 * 2. Build-time: NEXT_PUBLIC_TENANT_SLUG (platform hosts: demo, app, …)
 * 3. Default: test (local dev)
 */
export function getTenantSlug(): string {
  if (typeof window !== "undefined") {
    const base = process.env.NEXT_PUBLIC_TENANT_BASE_DOMAIN?.trim().toLowerCase();
    if (base) {
      const hostname = window.location.hostname.split(":")[0].toLowerCase();
      if (hostname.endsWith(`.${base}`)) {
        const slug = hostname.slice(0, -(base.length + 1)).toLowerCase();
        if (slug && !RESERVED_SUBDOMAINS.has(slug)) {
          return slug;
        }
      }
    }
  }
  return process.env.NEXT_PUBLIC_TENANT_SLUG || "test";
}

/** @deprecated Prefer getTenantSlug() — kept for imports that expect a constant at module load. */
export const TENANT_SLUG = process.env.NEXT_PUBLIC_TENANT_SLUG || "test";
