"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { LogOut } from "lucide-react";

type NavItem = { href: string; label: string; icon?: string };

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
    <div className="portal-device-stage">
      <div className="portal-device-frame">
        <div className="portal-device-notch" aria-hidden />
        <div className="portal-shell">
          <header className="portal-header">
            <div>
              <div style={{ fontWeight: 800, fontSize: 18 }}>{title}</div>
              {subtitle && (
                <div style={{ fontSize: 13, color: "var(--text-muted)" }}>{subtitle}</div>
              )}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, color: "var(--text-muted)", maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {user?.full_name}
              </span>
              <button type="button" className="btn btn-ghost" onClick={handleLogout} aria-label="Logout">
                <LogOut size={18} />
              </button>
            </div>
          </header>

          <main className="portal-main">{children}</main>

          <nav className="portal-bottom-nav">
            {nav.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`portal-nav-item${active ? " active" : ""}`}
                >
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
      <p className="portal-device-caption">Mobile app preview — same experience on parent & student phones</p>
    </div>
  );
}
