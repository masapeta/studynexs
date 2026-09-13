"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Send, Sparkles } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { roleLabel, type UserPermissions } from "@/lib/permissions";
import { createWorkspaceTurn } from "@/lib/workspace-client";
import type { WorkspaceResponse } from "@/lib/workspace-types";
import {
  WORKSPACE_ACTIONS,
  WORKSPACE_PROMPTS,
  roleToWorkspaceRole,
  type WorkspaceActionDef,
} from "@/lib/workspace-actions";
import { classifyIntent, type DataQuery, type NavTarget } from "@/lib/workspace-intent";

function formatMetric(value: unknown, format?: "number" | "money" | "percent"): string {
  if (value === null || value === undefined) return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(num)) return String(value);
  if (format === "money") return `₹${num.toLocaleString("en-IN")}`;
  if (format === "percent") return `${Math.round(num)}%`;
  return num.toLocaleString("en-IN");
}
import { TeacherWorkspaceBlockRenderer } from "@/components/teaching/TeacherWorkspaceBlockRenderer";
import { WorkspaceSlimNav, type SlimNavKey } from "./WorkspaceSlimNav";
import { WorkspaceTopBar } from "./WorkspaceTopBar";
import { ActionWidgetGrid } from "./ActionWidgetGrid";
import { WorkflowPanel, type WorkflowPanelState } from "./WorkflowPanel";
import { WorkspaceModulesDrawer, type DrawerGroup } from "./WorkspaceModulesDrawer";

interface Props {
  userName: string;
  role: string;
  permissions: UserPermissions | null;
  institution: string;
  modules: Record<string, boolean>;
  /** Where the slim-nav Settings button navigates. */
  settingsHref?: string;
  /** Where the slim-nav Home button navigates (portal home). */
  homeHref?: string;
  /** Custom module groups for the drawer (parent/student). */
  drawerGroups?: DrawerGroup[];
  /** When set, the center renders this page content inside the shell instead
   *  of the command center (keeps one consistent chrome across all routes). */
  children?: React.ReactNode;
  /** Title shown in the topbar when rendering page content. */
  pageTitle?: string;
}

export function WorkspaceRoot({
  userName,
  role,
  permissions,
  institution,
  modules,
  settingsHref = "/dashboard/settings",
  homeHref = "/dashboard",
  drawerGroups,
  children,
  pageTitle,
}: Props) {
  const router = useRouter();
  const wsRole = roleToWorkspaceRole(role);
  const actions = WORKSPACE_ACTIONS[wsRole];
  const prompts = WORKSPACE_PROMPTS[wsRole];

  const [navActive, setNavActive] = useState<SlimNavKey>("home");
  const [modulesOpen, setModulesOpen] = useState(false);
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [response, setResponse] = useState<WorkspaceResponse | null>(null);
  const [error, setError] = useState("");
  const [guide, setGuide] = useState<{ query: string; suggestions: NavTarget[] } | null>(null);
  const [dataCard, setDataCard] = useState<{
    query: DataQuery;
    metrics: Array<{ label: string; value: string }>;
    checkedAt: string;
  } | null>(null);
  const [panel, setPanel] = useState<WorkflowPanelState | null>(null);
  const streamRef = useRef<HTMLDivElement>(null);

  const isPageMode = Boolean(children);

  const title = useMemo(() => {
    if (isPageMode) return pageTitle || "Workspace";
    if (response?.message?.title) return response.message.title;
    return "Command workspace";
  }, [isPageMode, pageTitle, response]);

  const runData = useCallback(async (query: DataQuery) => {
    setSubmitting(true);
    setError("");
    setResponse(null);
    setGuide(null);
    setDataCard(null);
    try {
      const res = await api<{ data: Record<string, unknown> }>(query.endpoint);
      const payload = res?.data ?? {};
      const metrics = query.metrics.map((m) => ({
        label: m.label,
        value: formatMetric(payload[m.from], m.format),
      }));
      setDataCard({ query, metrics, checkedAt: new Date().toISOString() });
      setTimeout(() => streamRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
    } catch (err) {
      setError(getApiErrorMessage(err, "Couldn't load that data right now."));
    } finally {
      setSubmitting(false);
    }
  }, []);

  const runIntent = useCallback(
    async (intent: string, action?: WorkspaceActionDef) => {
      setSubmitting(true);
      setError("");
      setResponse(null);
      setGuide(null);
      setDataCard(null);
      if (action) {
        setPanel({ action, status: "running", response: null });
      }
      try {
        const next = await createWorkspaceTurn({ mode: "read", text: intent });
        setResponse(next);
        if (action) {
          setPanel({ action, status: "verified", response: next });
        }
        setTimeout(() => streamRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
      } catch (err) {
        const message = getApiErrorMessage(err, "StudyNexs could not complete that request.");
        setError(message);
        if (action) {
          setPanel({ action, status: "error", error: message });
        }
      } finally {
        setSubmitting(false);
      }
    },
    []
  );

  const submitComposer = useCallback(
    (value?: string) => {
      const requestText = (value ?? text).trim();
      if (!requestText) return;

      // Decide intent BEFORE any backend call: navigate, pull data, or guide.
      const decision = classifyIntent(requestText, wsRole, permissions);
      if (decision.kind === "navigate") {
        setText("");
        router.push(decision.target.href);
        return;
      }
      if (decision.kind === "data") {
        void runData(decision.query);
        return;
      }
      if (decision.kind === "guide") {
        setResponse(null);
        setError("");
        setPanel(null);
        setDataCard(null);
        setGuide({ query: requestText, suggestions: decision.suggestions });
        setTimeout(() => streamRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
        return;
      }
      void runIntent(decision.text);
    },
    [text, runIntent, runData, wsRole, permissions, router]
  );

  // Every action card is live: run its intent through the same router.
  const handleRunAction = useCallback(
    (action: WorkspaceActionDef) => {
      submitComposer(action.intent);
    },
    [submitComposer]
  );

  const handleNav = useCallback(
    (key: SlimNavKey) => {
      setNavActive(key);
      if (key === "home") {
        router.push(homeHref);
        return;
      }
      if (key === "new-chat") {
        if (isPageMode) {
          router.push(homeHref);
          return;
        }
        setResponse(null);
        setError("");
        setGuide(null);
        setDataCard(null);
        setPanel(null);
        setText("");
      }
    },
    [router, homeHref, isPageMode]
  );

  return (
    <div className={`sn-ws${panel ? " sn-ws--panel-open" : ""}`}>
      <WorkspaceSlimNav
        active={navActive}
        brand={institution || "StudyNexs"}
        onSelect={handleNav}
        onOpenModules={() => setModulesOpen(true)}
        onOpenSettings={() => router.push(settingsHref)}
      />

      <div className="sn-ws-center">
        <WorkspaceTopBar title={title} roleLabel={roleLabel(role)} institution={institution} />

        {isPageMode ? (
          <div className="sn-ws-scroll" style={{ paddingBottom: 40 }}>
            <div className="sn-ws-page">{children}</div>
          </div>
        ) : (
          <>
        <div className="sn-ws-scroll">
          <div className="sn-ws-canvas">
            <div className="sn-ws-hero">
              <div className="sn-ws-hero__badge">
                <Sparkles size={26} />
              </div>
              <h1 className="sn-ws-hero__title">How can StudyNexs help your academic day?</h1>
              <p className="sn-ws-hero__sub">
                Ask about classes, attendance, assignments, exams, marks, fees, certificates,
                policies, or student progress.
              </p>
            </div>

            {/* Prompt chips */}
            <div>
              <div className="sn-ws-chips">
                {prompts.map((p) => (
                  <button
                    key={p}
                    type="button"
                    className="sn-ws-chip"
                    onClick={() => {
                      setText(p);
                      submitComposer(p);
                    }}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Governed action widgets */}
            <div>
              <div className="sn-ws-label">Quick actions</div>
              <ActionWidgetGrid actions={actions} onRun={handleRunAction} />
            </div>

            {/* Response stream */}
            {error ? (
              <div
                className="card"
                style={{
                  margin: 0,
                  padding: 16,
                  background: "var(--danger-light)",
                  border: "1px solid color-mix(in srgb, var(--danger) 30%, transparent)",
                  color: "var(--danger)",
                  fontSize: 14,
                }}
              >
                {error}
              </div>
            ) : null}

            {response ? (
              <div className="card" style={{ margin: 0, padding: 22 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 12,
                    borderBottom: "1px solid var(--border)",
                    paddingBottom: 14,
                    marginBottom: 16,
                  }}
                >
                  <h3 style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)" }}>
                    {response.message.title}
                  </h3>
                  {response.verification?.status === "verified" ? (
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: "var(--success)",
                        background: "var(--success-light)",
                        border: "1px solid color-mix(in srgb, var(--success) 30%, transparent)",
                        padding: "4px 10px",
                        borderRadius: 999,
                      }}
                    >
                      Verified
                    </span>
                  ) : null}
                </div>
                <p style={{ fontSize: 14, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 18 }}>
                  {response.message.summary}
                </p>
                <div style={{ display: "grid", gap: 16 }}>
                  <TeacherWorkspaceBlockRenderer blocks={response.blocks} />
                </div>
                <div ref={streamRef} />
              </div>
            ) : null}

            {dataCard ? (
              <div className="card" style={{ margin: 0, padding: 22 }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 12,
                    borderBottom: "1px solid var(--border)",
                    paddingBottom: 14,
                    marginBottom: 16,
                  }}
                >
                  <h3 style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)" }}>
                    {dataCard.query.title}
                  </h3>
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: "var(--success)",
                      background: "var(--success-light)",
                      border: "1px solid color-mix(in srgb, var(--success) 30%, transparent)",
                      padding: "4px 10px",
                      borderRadius: 999,
                    }}
                  >
                    Verified
                  </span>
                </div>
                <div
                  style={{
                    display: "grid",
                    gap: 12,
                    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
                  }}
                >
                  {dataCard.metrics.map((m) => (
                    <div
                      key={m.label}
                      style={{
                        border: "1px solid var(--border)",
                        borderRadius: 12,
                        padding: "14px 16px",
                        background: "var(--bg)",
                      }}
                    >
                      <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{m.label}</div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: "var(--text-primary)" }}>
                        {m.value}
                      </div>
                    </div>
                  ))}
                </div>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 10,
                    marginTop: 16,
                    flexWrap: "wrap",
                  }}
                >
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Source: {dataCard.query.source} · checked{" "}
                    {new Date(dataCard.checkedAt).toLocaleTimeString()}
                  </span>
                  {dataCard.query.href ? (
                    <button
                      type="button"
                      className="btn btn-outline"
                      style={{ width: "auto", padding: "7px 14px" }}
                      onClick={() => router.push(dataCard.query.href!)}
                    >
                      {dataCard.query.hrefLabel ?? "Open"}
                    </button>
                  ) : null}
                </div>
                <div ref={streamRef} />
              </div>
            ) : null}

            {guide ? (
              <div className="card" style={{ margin: 0, padding: 22 }}>
                <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 16 }}>
                  <span
                    style={{
                      display: "inline-flex",
                      width: 36,
                      height: 36,
                      borderRadius: 10,
                      alignItems: "center",
                      justifyContent: "center",
                      background: "var(--accent-50)",
                      color: "var(--accent-dark)",
                      flexShrink: 0,
                    }}
                  >
                    <Sparkles size={18} />
                  </span>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
                      I can take you to the right place
                    </div>
                    <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 3 }}>
                      I don&apos;t have a verified answer for “{guide.query}” yet. Here&apos;s where
                      that usually lives — pick one and I&apos;ll open it.
                    </p>
                  </div>
                </div>
                <div
                  style={{
                    display: "grid",
                    gap: 8,
                    gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                  }}
                >
                  {guide.suggestions.map((s) => (
                    <button
                      key={s.href}
                      type="button"
                      className="card"
                      onClick={() => {
                        setGuide(null);
                        router.push(s.href);
                      }}
                      style={{
                        margin: 0,
                        padding: "12px 14px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 10,
                        cursor: "pointer",
                        textAlign: "left",
                      }}
                    >
                      <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)" }}>
                        {s.label}
                      </span>
                      <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Open</span>
                    </button>
                  ))}
                </div>
                <div ref={streamRef} />
              </div>
            ) : null}

            {submitting ? (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: 18,
                  color: "var(--text-muted)",
                  fontSize: 14,
                }}
              >
                <Sparkles size={16} style={{ color: "var(--accent)" }} />
                Orchestrating governed services…
              </div>
            ) : null}
          </div>
        </div>

        {/* Composer */}
        <div className="sn-ws-composer-wrap">
          <div className="sn-ws-composer">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submitComposer();
                }
              }}
              disabled={submitting}
              rows={2}
              placeholder="Ask StudyNexs anything…"
            />
            <button
              type="button"
              className="sn-ws-composer__send"
              disabled={submitting || !text.trim()}
              onClick={() => submitComposer()}
              aria-label="Send message"
            >
              <Send size={18} strokeWidth={2.3} />
            </button>
          </div>
        </div>
          </>
        )}
      </div>

      {panel ? <WorkflowPanel state={panel} onClose={() => setPanel(null)} /> : null}

      <WorkspaceModulesDrawer
        open={modulesOpen}
        permissions={permissions}
        modules={modules}
        groups={drawerGroups}
        onClose={() => setModulesOpen(false)}
      />
    </div>
  );
}
