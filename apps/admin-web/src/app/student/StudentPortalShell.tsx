"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePathForRole, portalFromRole } from "@/lib/portal";
import { PortalEntryLoading } from "@/components/brand";

export function StudentPortalShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login?portal=student");
      return;
    }
    const portal = portalFromRole(user.role);
    if (portal !== "student" && portal !== "staff") {
      router.replace(homePathForRole(user.role));
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return <PortalEntryLoading portal="student" />;
  }

  return <>{children}</>;
}
