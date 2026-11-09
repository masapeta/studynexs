"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { applyThemeColor, DEFAULT_ACCENT, getStoredThemeColor, normalizeThemeColor } from "@/lib/theme";
import { PORTAL_ROLES, portalHomeForRole } from "@/lib/permissions";
import { SkipLink } from "@/components/a11y/SkipLink";
import { RouteGuard } from "@/components/RouteGuard";
import { AppBackground } from "@/components/AppBackground";
import { NAV_GROUPS } from "@/lib/nav-groups";
import { DemoDataBanner } from "@/components/DemoDataBanner";
import { PortalEntryLoading } from "@/components/brand";
import { AppShell } from "@/components/shell/AppShell";
import { AssistantProvider } from "@/components/assistant/AssistantProvider";
import { navAllowed } from "@/lib/permissions";
import { personaForPermissions, visibleNavGroups } from "@/lib/nav-groups";

/** Human title for the workspace topbar, derived from the nav registry. */
function pageTitleForPath(pathname: string): string {
  if (pathname === "/dashboard") return "Home";
  if (pathname.startsWith("/dashboard/assistant")) return "Ask StudyNexs";
  let best = "";
  let bestLen = -1;
  for (const group of NAV_GROUPS) {
    for (const item of group.items) {
      if (
        (pathname === item.href || pathname.startsWith(`${item.href}/`)) &&
        item.href.length > bestLen
      ) {
        best = item.label;
        bestLen = item.href.length;
      }
    }
  }
  return best || "Workspace";
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const { user, permissions, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [modules, setModules] = useState<Record<string, boolean>>({});
  // Empty until /school/profile responds — never show a fabricated school name.
  const [schoolName, setSchoolName] = useState("");

  const isPortalUser = permissions ? PORTAL_ROLES.has(permissions.role) : false;

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (!loading && permissions && isPortalUser) {
      router.replace(portalHomeForRole(permissions.role));
    }
  }, [loading, permissions, isPortalUser, router]);

  useEffect(() => {
    if (user && permissions && !isPortalUser) {
      api("/api/v1/school/profile")
        .then((r) => {
          if (normalizeThemeColor(r.data?.theme_color)) {
            applyThemeColor(r.data.theme_color, { persist: true });
          } else {
            applyThemeColor(getStoredThemeColor() ?? DEFAULT_ACCENT, { persist: false });
          }
          setModules(r.data?.enabled_modules || {});
          if (r.data?.name) setSchoolName(r.data.name);
        })
        .catch(() => {});
    }
  }, [user, permissions, isPortalUser]);

  useEffect(() => {
    const onModules = (e: Event) => setModules((e as CustomEvent).detail || {});
    window.addEventListener("sn-modules", onModules);
    return () => window.removeEventListener("sn-modules", onModules);
  }, []);

  if (loading || isPortalUser) {
    return <PortalEntryLoading portal="admin" />;
  }

  if (!user) return null;

  const persona = personaForPermissions(permissions);
  const groups = visibleNavGroups(permissions, modules, navAllowed);
  const showMyClasses = persona === "incharge" || persona === "teacher";

  return (
    <div className="sn-app">
      <SkipLink />
      <AppBackground />
      <DemoDataBanner />
      <main id="main-content" tabIndex={-1}>
        <AssistantProvider base="/dashboard">
          <AppShell
            title={pageTitleForPath(pathname)}
            institution={schoolName.trim()}
            homeHref="/dashboard"
            groups={groups}
            myClassesHref={showMyClasses ? "/dashboard#my-classes" : undefined}
            settingsHref={permissions?.can_use_settings ? "/dashboard/settings" : undefined}
            staffSearch
            permissions={permissions}
          >
            <RouteGuard>{children}</RouteGuard>
          </AppShell>
        </AssistantProvider>
      </main>
    </div>
  );
}
