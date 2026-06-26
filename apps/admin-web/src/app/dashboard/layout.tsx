"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { applyThemeColor, DEFAULT_ACCENT, getStoredThemeColor, normalizeThemeColor } from "@/lib/theme";
import { navAllowed, PORTAL_ROLES, portalHomeForRole, type UserPermissions } from "@/lib/permissions";
import { RouteGuard } from "@/components/RouteGuard";
import { AppBackground } from "@/components/AppBackground";
import { NAV_GROUPS, DEFAULT_OFF_MODULES } from "@/lib/nav-groups";
import { TopBar } from "@/components/layout/TopBar";
import { LogOut } from "lucide-react";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, permissions, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [modules, setModules] = useState<Record<string, boolean>>({});
  const [schoolName, setSchoolName] = useState("Greenwood Public School");
  const [academicLabel, setAcademicLabel] = useState("Academic year 2025–26 · Term 1");

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
          const ay = r.data?.current_academic_year;
          if (ay?.label) setAcademicLabel(`${ay.label} · Term 1`);
        })
        .catch(() => {});
    }
  }, [user, permissions, isPortalUser]);

  useEffect(() => {
    const onModules = (e: Event) => setModules((e as CustomEvent).detail || {});
    window.addEventListener("sn-modules", onModules);
    return () => window.removeEventListener("sn-modules", onModules);
  }, []);

  const moduleVisible = (m?: string) => {
    if (!m) return true;
    if (DEFAULT_OFF_MODULES.has(m)) return modules[m] === true;
    return modules[m] !== false;
  };

  const itemVisible = (href: string, perm?: keyof UserPermissions) => {
    if (perm && permissions && !permissions[perm]) return false;
    return navAllowed(href, permissions);
  };

  const isActive = (href: string) =>
    href === "/dashboard" ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  if (loading || isPortalUser) {
    return (
      <div className="sn-app loading-screen">
        <AppBackground />
        <div className="spinner" />
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  const nameParts = schoolName.split(" ");
  const line1 = nameParts.slice(0, 1).join(" ") || "Greenwood";
  const line2 = nameParts.slice(1).join(" ") || "Public School";

  return (
    <div className="sn-app">
      <AppBackground />
      <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">G</div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-line">{line1}</span>
            <span className="sidebar-brand-line muted">{line2}</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {NAV_GROUPS.map((group) => {
            const items = group.items.filter(
              (item) => moduleVisible(item.module) && itemVisible(item.href, item.perm)
            );
            if (!items.length) return null;
            return (
              <div key={group.label} className="sidebar-nav-group">
                <div className="sidebar-nav-group-label">{group.label}</div>
                {items.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`nav-item ${isActive(item.href) ? "active" : ""}`}
                    >
                      <Icon className="nav-icon" size={19} strokeWidth={1.9} />
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="nav-item"
            onClick={logout}
          >
            <LogOut className="nav-icon" size={19} strokeWidth={1.9} />
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <TopBar
          userName={user.full_name}
          userRole={user.role}
          academicLabel={academicLabel}
          showSettings={navAllowed("/dashboard/settings", permissions)}
        />

        <div className="page-content">
          <RouteGuard>{children}</RouteGuard>
        </div>
      </main>
      </div>
    </div>
  );
}
