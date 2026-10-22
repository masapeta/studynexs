"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Send, Sparkles, MessageSquare } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api";
import { roleLabel, type UserPermissions } from "@/lib/permissions";
import {
  WORKSPACE_ACTIONS,
  WORKSPACE_PROMPTS,
  roleToWorkspaceRole,
  type WorkspaceActionDef,
} from "@/lib/workspace-actions";
import {
  assistantTurn,
  getChatSession,
  getJob,
  listChatSessions,
  type AssistantBlock,
  type ChatSessionSummary,
} from "@/lib/assistant-client";
import { workflowIsRunning } from "./assistant-block-logic";
import { AssistantBlockView } from "./AssistantBlockView";
import { WorkspaceSlimNav, type SlimNavKey } from "./WorkspaceSlimNav";
import { WorkspaceTopBar } from "./WorkspaceTopBar";
import { ActionWidgetGrid } from "./ActionWidgetGrid";
import { WorkspaceModulesDrawer, type DrawerGroup } from "./WorkspaceModulesDrawer";

interface Props {
  userName: string;
  role: string;
  permissions: UserPermissions | null;
  institution: string;
  modules: Record<string, boolean>;
  settingsHref?: string;
  homeHref?: string;
  drawerGroups?: DrawerGroup[];
  children?: React.ReactNode;
  pageTitle?: string;
}

/** One rendered conversation turn (user prompt or assistant block). */
interface Turn {
  id: string;
  role: "user" | "assistant";
  text?: string;
  block?: AssistantBlock;
}

export function WorkspaceRoot({
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
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const streamRef = useRef<HTMLDivElement>(null);

  const isPageMode = Boolean(children);
  const hasConversation = turns.length > 0;

  const title = useMemo(() => {
    if (isPageMode) return pageTitle || "Workspace";
    return "Command workspace";
  }, [isPageMode, pageTitle]);

  const scrollToEnd = useCallback(() => {
    setTimeout(() => streamRef.current?.scrollIntoView({ behavior: "smooth" }), 80);
  }, []);

  // Timers for in-flight async workflows (e.g. question-paper generation), keyed by turn id, so
  // unmount / new-chat can cancel them and a stale poll never mutates a turn that's gone.
  const pollTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const clearPoll = useCallback((turnId: string) => {
    const t = pollTimers.current.get(turnId);
    if (t) {
      clearTimeout(t);
      pollTimers.current.delete(turnId);
    }
  }, []);

  useEffect(() => {
    const timers = pollTimers.current;
    return () => {
      timers.forEach((t) => clearTimeout(t));
      timers.clear();
    };
  }, []);

  /**
   * Poll a queued/running workflow's backing job until it finishes, then replace that turn's
   * block with an honest outcome. We NEVER show success speculatively — only what the job reports.
   */
  const pollWorkflowJob = useCallback(
    (turnId: string, jobId: string, baseBlock: AssistantBlock) => {
      const MAX_ATTEMPTS = 60; // ~2 min — then we stop and tell the user honestly
      clearPoll(turnId);

      const schedule = (attempt: number) => {
        const timer = setTimeout(
          async () => {
            try {
              const job = await getJob(jobId);
              if (job.status === "done") {
                const paperId = job.result?.paper_id as string | undefined;
                setTurns((prev) =>
                  prev.map((t) =>
                    t.id === turnId
                      ? {
                          ...t,
                          block: {
                            ...baseBlock,
                            workflow_state: "waiting_for_approval",
                            message: "Your question paper is ready to review and approve.",
                            actions: paperId
                              ? [
                                  {
                                    label: "Review",
                                    href: `/dashboard/question-papers/${paperId}`,
                                  },
                                ]
                              : baseBlock.actions,
                            summary: { ...(baseBlock.summary ?? {}), paper_id: paperId ?? null },
                          },
                        }
                      : t
                  )
                );
                clearPoll(turnId);
                return;
              }
              if (job.status === "failed") {
                setTurns((prev) =>
                  prev.map((t) =>
                    t.id === turnId
                      ? {
                          ...t,
                          block: {
                            kind: "error",
                            title: "Generation failed",
                            message:
                              "The question paper couldn't be generated. Please try again.",
                          },
                        }
                      : t
                  )
                );
                clearPoll(turnId);
                return;
              }
              if (attempt + 1 >= MAX_ATTEMPTS) {
                setTurns((prev) =>
                  prev.map((t) =>
                    t.id === turnId
                      ? {
                          ...t,
                          block: {
                            ...baseBlock,
                            message:
                              "Still generating — this is taking longer than usual. " +
                              "You can keep working; check back shortly.",
                          },
                        }
                      : t
                  )
                );
                clearPoll(turnId);
                return;
              }
              schedule(attempt + 1);
            } catch {
              // Transient read failure (e.g. a refresh in flight): back off and retry, bounded.
              if (attempt + 1 < MAX_ATTEMPTS) schedule(attempt + 1);
              else clearPoll(turnId);
            }
          },
          attempt === 0 ? 1200 : 2000
        );
        pollTimers.current.set(turnId, timer);
      };

      schedule(0);
    },
    [clearPoll]
  );

  const send = useCallback(
    async (value?: string) => {
      const requestText = (value ?? text).trim();
      if (!requestText || submitting) return;
      setText("");
      setError("");
      setSubmitting(true);
      const userTurn: Turn = { id: `u-${Date.now()}`, role: "user", text: requestText };
      setTurns((prev) => [...prev, userTurn]);
      scrollToEnd();
      try {
        const res = await assistantTurn(requestText, sessionId);
        setSessionId(res.session_id);
        // A pure navigate result: go to the page instead of showing a card.
        if (res.block?.kind === "navigate" && res.block.href) {
          router.push(res.block.href);
          return;
        }
        const assistantId = `a-${Date.now()}`;
        setTurns((prev) => [
          ...prev,
          { id: assistantId, role: "assistant", block: res.block },
        ]);
        // An async workflow (e.g. question-paper generation) returns QUEUED with a job id — poll
        // the existing job endpoint and update this turn in place when it finishes.
        const block = res.block;
        const jobId =
          block?.kind === "workflow" && workflowIsRunning(block.workflow_state)
            ? (block.summary?.job_id as string | undefined)
            : undefined;
        if (jobId && block) pollWorkflowJob(assistantId, jobId, block);
        scrollToEnd();
      } catch (err) {
        setError(getApiErrorMessage(err, "StudyNexs could not complete that request."));
      } finally {
        setSubmitting(false);
      }
    },
    [text, submitting, sessionId, router, scrollToEnd, pollWorkflowJob] 
  );

  const handleRunAction = useCallback(
    (action: WorkspaceActionDef) => {
      void send(action.intent);
    },
    [send]
  );

  const cancelAllPolls = useCallback(() => {
    pollTimers.current.forEach((t) => clearTimeout(t));
    pollTimers.current.clear();
  }, []);

  const startNewChat = useCallback(() => {
    cancelAllPolls();
    setTurns([]);
    setError("");
    setSessionId(null);
    setText("");
    setHistoryOpen(false);
  }, [cancelAllPolls]);

  const openHistory = useCallback(async () => {
    setHistoryOpen(true);
    try {
      setSessions(await listChatSessions());
    } catch {
      setSessions([]);
    }
  }, []);

  const loadSession = useCallback(
    async (id: string) => {
      cancelAllPolls();
      setHistoryOpen(false);
      setError("");
      try {
        const msgs = await getChatSession(id);
        setSessionId(id);
        setTurns(
          msgs.map((m, i) => ({
            id: `h-${i}`,
            role: m.role,
            text: m.role === "user" ? m.text : undefined,
            block: m.role === "assistant" ? m.payload ?? undefined : undefined,
          }))
        );
        scrollToEnd();
      } catch {
        setError("Couldn't load that conversation.");
      }
    },
    [scrollToEnd, cancelAllPolls]
  );

  const handleNav = useCallback(
    (key: SlimNavKey) => {
      setNavActive(key);
      if (key === "home") {
        if (isPageMode) router.push(homeHref);
        else startNewChat();
        return;
      }
      if (key === "new-chat") {
        if (isPageMode) router.push(homeHref);
        else startNewChat();
        return;
      }
      if (key === "history") {
        if (isPageMode) {
          router.push(homeHref);
          return;
        }
        void openHistory();
      }
    },
    [router, homeHref, isPageMode, startNewChat, openHistory]
  );

  useEffect(() => {
    if (!historyOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setHistoryOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [historyOpen]);

  return (
    <div className="sn-ws">
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
                {!hasConversation ? (
                  <>
                    <div className="sn-ws-hero">
                      <div className="sn-ws-hero__badge">
                        <Sparkles size={26} />
                      </div>
                      <h1 className="sn-ws-hero__title">
                        How can StudyNexs help your academic day?
                      </h1>
                      <p className="sn-ws-hero__sub">
                        Ask about classes, attendance, assignments, exams, marks, fees,
                        certificates, policies, or student progress.
                      </p>
                    </div>

                    <div>
                      <div className="sn-ws-chips">
                        {prompts.map((p) => (
                          <button
                            key={p}
                            type="button"
                            className="sn-ws-chip"
                            onClick={() => void send(p)}
                          >
                            {p}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <div className="sn-ws-label">Quick actions</div>
                      <ActionWidgetGrid actions={actions} onRun={handleRunAction} />
                    </div>
                  </>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {turns.map((turn) =>
                      turn.role === "user" ? (
                        <div
                          key={turn.id}
                          style={{ display: "flex", justifyContent: "flex-end" }}
                        >
                          <div
                            style={{
                              maxWidth: "80%",
                              background: "var(--accent-50)",
                              color: "var(--text-primary)",
                              border:
                                "1px solid color-mix(in srgb, var(--accent) 20%, transparent)",
                              borderRadius: 14,
                              padding: "10px 14px",
                              fontSize: 14,
                            }}
                          >
                            {turn.text}
                          </div>
                        </div>
                      ) : turn.block ? (
                        <AssistantBlockView
                          key={turn.id}
                          block={turn.block}
                          onSelect={(t) => void send(t)}
                        />
                      ) : null
                    )}
                  </div>
                )}

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
                    Thinking…
                  </div>
                ) : null}

                <div ref={streamRef} />
              </div>
            </div>

            <div className="sn-ws-composer-wrap">
              <div className="sn-ws-composer">
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void send();
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
                  onClick={() => void send()}
                  aria-label="Send message"
                >
                  <Send size={18} strokeWidth={2.3} />
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {historyOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Chat history"
          style={{ position: "fixed", inset: 0, zIndex: 80, display: "flex" }}
        >
          <div
            onClick={() => setHistoryOpen(false)}
            aria-hidden
            style={{ position: "absolute", inset: 0, background: "rgba(15,23,42,0.35)" }}
          />
          <div
            style={{
              position: "relative",
              marginLeft: "auto",
              width: "min(400px, 92vw)",
              height: "100%",
              background: "var(--bg-card)",
              borderLeft: "1px solid var(--border)",
              boxShadow: "-12px 0 40px rgba(15,23,42,0.16)",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "16px 18px",
                borderBottom: "1px solid var(--border)",
              }}
            >
              <strong style={{ fontSize: 15, color: "var(--text-primary)" }}>Chat history</strong>
              <button
                type="button"
                onClick={() => setHistoryOpen(false)}
                aria-label="Close history"
                className="sn-ws-panel__close"
              >
                ✕
              </button>
            </div>
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: 8,
                display: "flex",
                flexDirection: "column",
                gap: 2,
              }}
            >
              {sessions.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: 14, padding: 12 }}>
                  No past conversations yet.
                </p>
              ) : (
                sessions.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => void loadSession(s.id)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      width: "100%",
                      padding: "10px 12px",
                      border: "none",
                      background: "transparent",
                      borderRadius: 10,
                      cursor: "pointer",
                      textAlign: "left",
                      transition: "background var(--transition)",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                  >
                    <MessageSquare
                      size={15}
                      style={{ color: "var(--text-muted)", flexShrink: 0 }}
                    />
                    <span
                      style={{
                        fontSize: 13,
                        fontWeight: 500,
                        color: "var(--text-primary)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        minWidth: 0,
                      }}
                    >
                      {s.title}
                    </span>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>
      ) : null}

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
