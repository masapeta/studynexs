"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePathForRole, portalFromRole } from "@/lib/portal";
import { PortalEntryLoading } from "@/components/brand";

export function TeacherPortalShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login?portal=teacher");
      return;
    }
    const portal = portalFromRole(user.role);
    if (portal !== "teacher" && portal !== "staff") {
      router.replace(homePathForRole(user.role));
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return <PortalEntryLoading portal="teacher" />;
  }

  return <>{children}</>;
}
