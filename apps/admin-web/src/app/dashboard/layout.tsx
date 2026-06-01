"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";
import { applyThemeColor } from "@/lib/theme";
import {
  LayoutDashboard, GraduationCap, Users, School, Sparkles, ClipboardCheck,
  FileText, Award, CalendarDays, Wallet, Megaphone, Settings as SettingsIcon, LogOut,
} from "lucide-react";

// Demo nav: only pages fully wired to the backend are shown. Remaining stub pages
// (library, events) are hidden until built so nothing reads "coming soon".
const NAV_ITEMS = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Students", href: "/dashboard/students", icon: GraduationCap },
  { label: "Staff", href: "/dashboard/staff", icon: Users },
  { label: "Classes", href: "/dashboard/classes", icon: School },
  { label: "AI Papers", href: "/dashboard/ai-papers", icon: Sparkles },
  { label: "Attendance", href: "/dashboard/attendance", icon: ClipboardCheck },
  { label: "Exams", href: "/dashboard/exams", icon: FileText },
  { label: "Report Cards", href: "/dashboard/report-cards", icon: Award },
  { label: "Timetable", href: "/dashboard/timetable", icon: CalendarDays },
  { label: "Finance", href: "/dashboard/finance", icon: Wallet },
  { label: "Notices", href: "/dashboard/notices", icon: Megaphone },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/");
    }
  }, [user, loading, router]);

  // Apply the school's brand colour (per-tenant theming).
  useEffect(() => {
    if (user) {
      api("/api/v1/school/profile")
        .then((r) => applyThemeColor(r.data?.theme_color))
        .catch(() => {});
    }
  }, [user]);

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p style={{ color: "var(--text-muted)" }}>Loading...</p>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo" style={{ padding: "24px 20px" }}>
          <Image
            src="/studynexs.png"
            alt="StudyNexs Logo"
            width={188}
            height={60}
            priority
            style={{ objectFit: "contain", height: 56, width: "auto" }}
          />
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`nav-item ${pathname === item.href ? "active" : ""}`}
              >
                <Icon className="nav-icon" size={19} strokeWidth={1.9} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <Link href="/dashboard/settings" className={`nav-item ${pathname === "/dashboard/settings" ? "active" : ""}`}>
            <SettingsIcon className="nav-icon" size={19} strokeWidth={1.9} />
            Settings
          </Link>
          <button
            className="nav-item"
            onClick={logout}
            style={{ width: "100%", border: "none", background: "none", textAlign: "left", font: "inherit" }}
          >
            <LogOut className="nav-icon" size={19} strokeWidth={1.9} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        {/* Header */}
        <header className="header">
          <button className="notification-bell">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <span className="notification-badge" />
          </button>
          <div className="header-user">
            <div className="header-avatar">
              {user.full_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="header-name">{user.full_name}</div>
              <div className="header-role">{user.role.replace("_", " ")}</div>
            </div>
          </div>
        </header>

        <div className="page-content">{children}</div>
      </main>
    </div>
  );
}
