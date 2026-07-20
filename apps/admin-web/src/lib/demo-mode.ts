import { getTenantSlug } from "@/lib/tenant";

const DEMO_TENANT_SLUGS = new Set(["test", "demo"]);

/** True when UI should show demo/sample-data warnings (Gate 1). */
export function isDemoMode(): boolean {
  if (process.env.NEXT_PUBLIC_DEMO_MODE === "true") return true;
  if (DEMO_TENANT_SLUGS.has(getTenantSlug())) return true;
  const env = process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || "";
  return env === "development";
}
