"use client";

import { useEffect, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { AppBackground } from "@/components/AppBackground";
import { SkipLink } from "@/components/a11y/SkipLink";
import { AppShell } from "@/components/shell/AppShell";
import { ChatPage } from "@/components/assistant/ChatPage";
import { AssistantProvider, useAssistantOptional } from "@/components/assistant/AssistantProvider";

export type NavItem = { href: string; label: string; icon?: LucideIcon };

/**
 * Parent/student portal page wrapper on the shared AppShell. The conversation lives in the
 * portal layout's AssistantProvider, so it survives navigation between portal pages.
 */
export default function PortalShell({
  title,
  subtitle,
  nav,
  chat = false,
  sessionId,
  children,
}: {
  title: string;
  subtitle?: string;
  nav: NavItem[];
  /** Retained for API compatibility; the responsive shell handles width. */
  wide?: boolean;
  /** Render the full-page conversation instead of page children. */
  chat?: boolean;
  /** With `chat`, restore this conversation (URL-addressable). */
  sessionId?: string;
  children?: React.ReactNode;
}) {
  const hasProvider = useAssistantOptional() !== null;
  const home = nav[0]?.href ?? "/";
  const inner = (
    <PortalShellInner title={title} subtitle={subtitle} nav={nav} chat={chat} sessionId={sessionId}>
      {children}
    </PortalShellInner>
  );
  if (hasProvider) return inner;
  const base = `/${home.split("/").filter(Boolean)[0] ?? "student"}`;
  return <AssistantProvider base={base}>{inner}</AssistantProvider>;
}

function PortalShellInner({
  title,
  subtitle,
  nav,
  chat,
  sessionId,
  children,
}: {
  title: string;
  subtitle?: string;
  nav: NavItem[];
  chat: boolean;
  sessionId?: string;
  children?: React.ReactNode;
}) {
  const { permissions } = useAuth();
  const [schoolName, setSchoolName] = useState("");
  const home = nav[0]?.href ?? "/";

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
        <AppShell
          title={title}
          institution={schoolName}
          homeHref={home}
          groups={[{ label: "Portal", items: nav.slice(1) }]}
          staffSearch={false}
          permissions={permissions}
        >
          {chat ? (
            <ChatPage sessionId={sessionId} />
          ) : (
            <div className="sn-ws-page">
              {subtitle ? (
                <p style={{ color: "var(--text-muted)", fontSize: 14, margin: "0 0 16px" }}>{subtitle}</p>
              ) : null}
              {children}
            </div>
          )}
        </AppShell>
      </main>
    </div>
  );
}
