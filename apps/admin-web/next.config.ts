import type { NextConfig } from "next";

/** Docker/OCI uses standalone; Cloudflare Pages / Vercel must not set it. */
const useStandalone =
  process.env.DEPLOY_TARGET === "oci" ||
  (process.env.DEPLOY_TARGET !== "cloudflare" &&
    process.env.DEPLOY_TARGET !== "vercel" &&
    !process.env.CF_PAGES);

const nextConfig: NextConfig = {
  ...(useStandalone ? { output: "standalone" as const } : {}),
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion"],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000",
  },
};

import { initOpenNextCloudflareForDev } from "@opennextjs/cloudflare";

export default nextConfig;

if (process.env.NODE_ENV === "development") {
  initOpenNextCloudflareForDev();
}
