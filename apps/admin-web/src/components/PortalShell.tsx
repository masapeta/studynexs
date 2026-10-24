"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import type { LucideIcon } from "lucide-react";
import { api } from "@/lib/api";
import { AppBackground } from "@/components/AppBackground";
import { WorkspaceRoot } from "@/components/workspace/WorkspaceRoot";
import { SkipLink } from "@/components/a11y/SkipLink";

export type NavItem = { href: string; label: string; icon?: LucideIcon };

/**
 * Portal shell for parent/student. Renders inside the unified responsive
 * WorkspaceRoot (3-zone on desktop, collapses to bottom-nav on mobile) so every
 * portal looks like one product. The `nav` config drives the slim rail, the
 * "All modules" drawer, and the mobile bottom nav; `children` render as the page.
 */
export default function PortalShell({
  title,
  subtitle,
  nav,
  chat = false,
  children,
}: {
  title: string;
  subtitle?: string;
  nav: NavItem[];
  /** Retained for API compatibility; the responsive shell handles width. */
  wide?: boolean;
  /** Render the native chat (no page children) instead of a portal page. */
  chat?: boolean;
  children?: React.ReactNode;
}) {
  const { user, permissions } = useAuth();
  const [schoolName, setSchoolName] = useState("");

  const home = nav[0]?.href ?? "/";
  const portalRoot = home.split("/").filter(Boolean)[0] ?? "";
  const settingsHref = `/${portalRoot}`;

  useEffect(() => {
    api<{ data: { school_name?: string } }>("/api/v1/portal/context")
      .then((r) => setSchoolName(r.data?.school_name ?? ""))
      .catch(() => {});
  }, []);

  return (
    <div className="sn-app">
      <SkipLink />
      <AppBackground />
      <main id="main-content" tabIndex={-1}>
        <WorkspaceRoot
          userName={user?.full_name ?? ""}
          role={user?.role ?? "student"}
          permissions={permissions}
          institution={schoolName}
          modules={{}}
          homeHref={home}
          settingsHref={settingsHref}
          drawerGroups={[{ label: "Portal", items: nav }]}
          pageTitle={chat ? undefined : title}
        >
          {chat ? undefined : (
            <>
              {subtitle ? (
                <p style={{ color: "var(--text-muted)", fontSize: 14, margin: "0 0 16px" }}>
                  {subtitle}
                </p>
              ) : null}
              {children}
            </>
          )}
        </WorkspaceRoot>
      </main>
    </div>
  );
}

