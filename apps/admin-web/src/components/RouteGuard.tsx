"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { routeAllowed, portalHomeForRole } from "@/lib/permissions";

/** Redirects when a user navigates directly to a route their role cannot access. */
export function RouteGuard({ children }: { children: React.ReactNode }) {
  const { permissions, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (loading || !permissions) return;
    // Match longest nav prefix (e.g. /dashboard/ai-papers)
    const blocked =
      pathname.startsWith("/dashboard") &&
      !routeAllowed(pathname, permissions);
    if (blocked) {
      router.replace(portalHomeForRole(permissions.role));
    }
  }, [loading, permissions, pathname, router]);

  return <>{children}</>;
}
