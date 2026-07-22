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

const PROSPECT_TENANT_KEY = "sn_prospect_tenant_slug";

/** Persist prospect tenant slug for API calls after self-guided provisioning (Stage 2B). */
export function setProspectTenantSlug(slug: string | null): void {
  if (typeof sessionStorage === "undefined") return;
  try {
    if (slug) sessionStorage.setItem(PROSPECT_TENANT_KEY, slug);
    else sessionStorage.removeItem(PROSPECT_TENANT_KEY);
  } catch {
    // Private mode — in-memory only for this tab via module cache below.
  }
  _prospectSlugCache = slug;
}

/** Clear prospect tenant override on logout so normal login uses the correct slug. */
export function clearProspectTenantSlug(): void {
  setProspectTenantSlug(null);
}

const DEMO_SESSION_TOKEN_KEY = "sn_demo_session_token";

export function setDemoSessionToken(token: string | null): void {
  if (typeof sessionStorage === "undefined") return;
  try {
    if (token) sessionStorage.setItem(DEMO_SESSION_TOKEN_KEY, token);
    else sessionStorage.removeItem(DEMO_SESSION_TOKEN_KEY);
  } catch {
    // ignore
  }
}

export function getDemoSessionToken(): string | null {
  if (typeof sessionStorage === "undefined") return null;
  try {
    return sessionStorage.getItem(DEMO_SESSION_TOKEN_KEY);
  } catch {
    return null;
  }
}

let _prospectSlugCache: string | null = null;

function readProspectTenantSlug(): string | null {
  if (_prospectSlugCache) return _prospectSlugCache;
  if (typeof sessionStorage === "undefined") return null;
  try {
    return sessionStorage.getItem(PROSPECT_TENANT_KEY);
  } catch {
    return null;
  }
}

/**
 * Resolve the school tenant slug for API calls.
 *
 * 1. Prospect session (Stage 2B self-guided demo)
 * 2. Runtime: {school}.studynexs.com → school (when NEXT_PUBLIC_TENANT_BASE_DOMAIN is set)
 * 3. Build-time: NEXT_PUBLIC_TENANT_SLUG (platform hosts: demo, app, …)
 * 4. Default: test (local dev)
 */
export function getTenantSlug(): string {
  const prospect = readProspectTenantSlug();
  if (prospect) return prospect;

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
