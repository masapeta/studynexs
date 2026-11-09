/** Deployment tier, inlined at build time from the deployment's NEXT_PUBLIC_DEPLOYMENT_TIER. */

export type DeploymentTier = "development" | "internal" | "staging" | "demo" | "production";

const TIERS: readonly DeploymentTier[] = ["development", "internal", "staging", "demo", "production"];

export function deploymentTier(): DeploymentTier {
  const raw = (process.env.NEXT_PUBLIC_DEPLOYMENT_TIER || "").trim().toLowerCase();
  if ((TIERS as readonly string[]).includes(raw)) return raw as DeploymentTier;
  // Unset tier is treated as production so a misconfigured deployment fails closed.
  return process.env.NODE_ENV === "development" ? "development" : "production";
}

export function isInternalDeploymentTier(): boolean {
  const tier = deploymentTier();
  return tier === "development" || tier === "internal";
}

/** Demo login picker: only on development/demo tiers and only when explicitly enabled. */
export function demoLoginEnabled(): boolean {
  const tier = deploymentTier();
  return (
    (tier === "development" || tier === "demo") &&
    process.env.NEXT_PUBLIC_DEMO_LOGIN_ENABLED === "true"
  );
}
