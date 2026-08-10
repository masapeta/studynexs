"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { LogOut } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { AppBackground } from "@/components/AppBackground";
import { DemoDataBanner } from "@/components/DemoDataBanner";

export type NavItem = { href: string; label: string; icon?: LucideIcon };

export default function PortalShell({
  title,
  subtitle,
  nav,
  children,
}: {
  title: string;
  subtitle?: string;
  nav: NavItem[];
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  async function handleLogout() {
    await logout();
    router.push("/");
  }

  return (
    <div className="sn-app portal-device-stage">
      <AppBackground />
      <div className="portal-device-frame">
        <div className="portal-shell">
          <DemoDataBanner />
          <header className="portal-header">
            <div>
              <div style={{ fontWeight: 800, fontSize: 17, letterSpacing: "-0.02em" }}>{title}</div>
              {subtitle && (
                <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 2 }}>{subtitle}</div>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  fontSize: 12,
                  color: "var(--text-muted)",
                  maxWidth: 100,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {user?.full_name}
              </span>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                style={{
                  width: 36,
                  height: 36,
                  padding: 0,
                  borderRadius: 12,
                  background: "rgba(255,255,255,0.5)",
                  border: "1px solid var(--sn-glass-border-soft, var(--border))",
                }}
                onClick={handleLogout}
                aria-label="Logout"
              >
                <LogOut size={17} />
              </button>
            </div>
          </header>

          <main className="portal-main">{children}</main>

          <nav className="portal-bottom-nav" aria-label="Portal navigation">
            {nav.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`portal-nav-item${active ? " active" : ""}`}
                >
                  {Icon && (
                    <span className="portal-nav-icon">
                      <Icon size={21} strokeWidth={active ? 2.5 : 2} />
                    </span>
                  )}
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
      <p className="portal-device-caption">StudyNexs portal</p>
    </div>
  );
}
