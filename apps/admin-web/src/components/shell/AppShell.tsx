"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { TopBar } from "@/components/layout/TopBar";
import { useAssistant } from "@/components/assistant/AssistantProvider";
import { AssistantPanel, BackToConversationChip } from "@/components/assistant/AskAI";
import { ConversationList } from "@/components/assistant/ConversationList";
import { RecordDrawer } from "@/components/assistant/RecordDrawer";
import { RoleNav, type ShellNavItem } from "./RoleNav";
import type { NavGroup } from "@/lib/nav-groups";
import type { UserPermissions } from "@/lib/permissions";

const COLLAPSE_KEY = "sn_nav_collapsed";

/**
 * One shell for every authenticated surface (staff + portals): persona nav, top bar,
 * page content, and the assistant (conversation state lives in AssistantProvider above this).
 */
export function AppShell({
  title,
  institution,
  homeHref,
  groups,
  myClassesHref,
  settingsHref,
  staffSearch,
  permissions,
  children,
}: {
  title: string;
  institution: string;
  homeHref: string;
  groups: NavGroup[] | { label: string; items: ShellNavItem[] }[];
  myClassesHref?: string;
  settingsHref?: string;
  staffSearch: boolean;
  permissions: UserPermissions | null;
  children: React.ReactNode;
}) {
  const { user, logout } = useAuth();
  const assistant = useAssistant();
  const [collapsed, setCollapsed] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  // Read the persisted preference after mount (SSR renders expanded; avoids hydration mismatch).
  useEffect(() => {
    let stored = false;
    try {
      stored = localStorage.getItem(COLLAPSE_KEY) === "1";
    } catch {
      // storage unavailable: default expanded
    }
    if (stored) queueMicrotask(() => setCollapsed(true));
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((c) => {
      try {
        localStorage.setItem(COLLAPSE_KEY, c ? "0" : "1");
      } catch {
        // ignore
      }
      return !c;
    });
  }, []);

  const closeHistory = useCallback(() => setHistoryOpen(false), []);

  return (
    <div className={`sn-shell${collapsed ? " sn-shell--collapsed" : ""}`}>
      <RoleNav
        brand={institution}
        homeHref={homeHref}
        chatHref={`${assistant.base}/assistant`}
        groups={groups}
        myClassesHref={myClassesHref}
        settingsHref={settingsHref}
        collapsed={collapsed}
        onToggleCollapsed={toggle}
        onNewChat={assistant.startNew}
        onOpenHistory={() => setHistoryOpen(true)}
      />
      <div className="sn-shell__main">
        <TopBar
          userName={user?.full_name ?? ""}
          userRole={user?.role ?? ""}
          academicLabel=""
          title={title}
          institution={institution}
          settingsHref={settingsHref ?? null}
          showSettings={Boolean(settingsHref)}
          search={staffSearch ? { permissions, conversationHref: assistant.conversationHref } : null}
          onLogout={logout}
        />
        <Suspense fallback={null}>
          <BackToConversationChip />
        </Suspense>
        <div className="sn-shell__content">{children}</div>
      </div>
      <AssistantPanel />
      <RecordDrawer />
      <ConversationList open={historyOpen} onClose={closeHistory} />
    </div>
  );
}
