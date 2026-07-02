"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePathForRole, portalFromRole } from "@/lib/portal";
import { AppBackground } from "@/components/AppBackground";

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
    return (
      <div className="sn-app loading-screen">
        <AppBackground />
        <div className="spinner" style={{ margin: "0 auto" }} />
      </div>
    );
  }

  return <>{children}</>;
}
