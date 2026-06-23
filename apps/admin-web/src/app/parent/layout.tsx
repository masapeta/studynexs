"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { homePathForRole, portalFromRole } from "@/lib/portal";

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/?portal=parent");
      return;
    }
    const portal = portalFromRole(user.role);
    if (portal !== "parent" && portal !== "staff") {
      router.replace(homePathForRole(user.role));
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return <div style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>;
  }

  return <>{children}</>;
}
