"use client";

import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { routeAllowed } from "@/lib/permissions";
import { AccessDenied } from "@/components/AccessDenied";

/**
 * Renders a page only when the user's role may access it. Children never mount while
 * blocked, so a forbidden page cannot fire its API calls. The backend remains the real gate.
 */
export function RouteGuard({ children }: { children: React.ReactNode }) {
  const { permissions, loading } = useAuth();
  const pathname = usePathname();

  if (loading || !permissions) {
    return (
      <div style={{ padding: 40, textAlign: "center" }} aria-busy="true">
        <div className="spinner" style={{ margin: "0 auto" }} />
      </div>
    );
  }

  if (pathname.startsWith("/dashboard") && !routeAllowed(pathname, permissions)) {
    return <AccessDenied pathname={pathname} role={permissions.role} />;
  }

  return <>{children}</>;
}
