"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { ApiError, getApiErrorMessage } from "@/lib/api";
import {
  assistantTurn,
  getChatSession,
  getJob,
  runAssistantAction,
  type AssistantBlock,
  type PageContext,
  type SemanticState,
} from "@/lib/assistant-client";
import { workflowIsRunning } from "@/components/workspace/assistant-block-logic";
import type { AssistantActionRequest } from "@/components/workspace/AssistantBlockView";

export interface Turn {
  id: string;
  role: "user" | "assistant";
  text?: string;
  block?: AssistantBlock;
}

export type RecordTarget = { kind: "student" | "class"; id: string; href: string };

interface AssistantContextValue {
  /** Portal root that owns conversation URLs: "/dashboard", "/parent" or "/student". */
  base: string;
  sessionId: string | null;
  turns: Turn[];
  submitting: boolean;
  error: string;
  notFound: boolean;
  semanticState: SemanticState | null;
  pageContext: PageContext | null;
  record: RecordTarget | null;
  send: (text: string, opts?: { pageContext?: PageContext | null }) => Promise<void>;
  open: (id: string) => Promise<void>;
  startNew: () => void;
  handleAction: (req: AssistantActionRequest) => Promise<void>;
  navigate: (href: string) => void;
  setPageContext: (ctx: PageContext | null) => void;
  closeRecord: () => void;
  conversationHref: (id: string) => string;
}

const AssistantContext = createContext<AssistantContextValue | null>(null);

const RECORD_RE = /^\/dashboard\/(students|classes)\/([0-9a-f-]{36})$/;

/** Owns the conversation above route content, so navigating never destroys it. */
export function AssistantProvider({ base, children }: { base: string; children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notFound, setNotFound] = useState(false);
  const [semanticState, setSemanticState] = useState<SemanticState | null>(null);
  const [pageContext, setPageContext] = useState<PageContext | null>(null);
  const [record, setRecord] = useState<RecordTarget | null>(null);
  const pollTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());
  const sessionRef = useRef<string | null>(null);
  useEffect(() => {
    sessionRef.current = sessionId;
  }, [sessionId]);
  const [pagePath, setPagePath] = useState(pathname);
  // Page context is per page: drop it (and any open record) when the route changes.
  if (pagePath !== pathname) {
    setPagePath(pathname);
    setPageContext(null);
    setRecord(null);
  }

  const conversationHref = useCallback((id: string) => `${base}/assistant/c/${id}`, [base]);

  const cancelAllPolls = useCallback(() => {
    pollTimers.current.forEach((t) => clearTimeout(t));
    pollTimers.current.clear();
  }, []);

  useEffect(() => cancelAllPolls, [cancelAllPolls]);

  const replaceTurn = useCallback((turnId: string, block: AssistantBlock) => {
    setTurns((prev) => prev.map((t) => (t.id === turnId ? { ...t, block } : t)));
  }, []);

  /** Poll an async workflow's job and report only what the job says (never speculative success). */
  const pollWorkflowJob = useCallback(
    (turnId: string, jobId: string, baseBlock: AssistantBlock) => {
      const MAX_ATTEMPTS = 60;
      const schedule = (attempt: number) => {
        const timer = setTimeout(async () => {
          try {
            const job = await getJob(jobId);
            if (job.status === "done") {
              const paperId = job.result?.paper_id as string | undefined;
              replaceTurn(turnId, {
                ...baseBlock,
                workflow_state: "waiting_for_approval",
                message: "Your question paper is ready to review and approve.",
                actions: paperId
                  ? [{ label: "Review", href: `/dashboard/question-papers/${paperId}` }]
                  : baseBlock.actions,
                summary: { ...(baseBlock.summary ?? {}), paper_id: paperId ?? null },
              });
              pollTimers.current.delete(turnId);
              return;
            }
            if (job.status === "failed") {
              replaceTurn(turnId, {
                kind: "error",
                title: "Generation failed",
                message: "The question paper couldn't be generated. Please try again.",
              });
              pollTimers.current.delete(turnId);
              return;
            }
            if (attempt + 1 >= MAX_ATTEMPTS) {
              replaceTurn(turnId, {
                ...baseBlock,
                message:
                  "Still generating — this is taking longer than usual. You can keep working; check back shortly.",
              });
              pollTimers.current.delete(turnId);
              return;
            }
            schedule(attempt + 1);
          } catch {
            if (attempt + 1 < MAX_ATTEMPTS) schedule(attempt + 1);
            else pollTimers.current.delete(turnId);
          }
        }, attempt === 0 ? 1200 : 2000);
        pollTimers.current.set(turnId, timer);
      };
      schedule(0);
    },
    [replaceTurn]
  );

  const send = useCallback(
    async (raw: string, opts?: { pageContext?: PageContext | null }) => {
      const text = raw.trim();
      if (!text || submitting) return;
      setError("");
      setNotFound(false);
      setSubmitting(true);
      setTurns((prev) => [...prev, { id: `u-${Date.now()}`, role: "user", text }]);
      try {
        const ctx = opts?.pageContext === undefined ? pageContext : opts.pageContext;
        const res = await assistantTurn(text, sessionRef.current, ctx);
        const isNew = res.session_id !== sessionRef.current;
        sessionRef.current = res.session_id;
        setSessionId(res.session_id);
        if (res.semantic_state !== undefined) setSemanticState(res.semantic_state ?? null);
        const assistantId = `a-${Date.now()}`;
        setTurns((prev) => [...prev, { id: assistantId, role: "assistant", block: res.block }]);
        const block = res.block;
        const jobId =
          block?.kind === "workflow" && workflowIsRunning(block.workflow_state)
            ? (block.summary?.job_id as string | undefined)
            : undefined;
        if (jobId && block) pollWorkflowJob(assistantId, jobId, block);
        // The full-page chat owns its URL; panels (Ask AI) keep the current page.
        if (isNew && window.location.pathname.startsWith(`${base}/assistant`)) {
          router.replace(conversationHref(res.session_id));
        }
      } catch (err) {
        setError(getApiErrorMessage(err, "StudyNexs could not complete that request."));
      } finally {
        setSubmitting(false);
      }
    },
    [submitting, pageContext, pollWorkflowJob, base, router, conversationHref]
  );

  const open = useCallback(
    async (id: string) => {
      if (id === sessionRef.current && turns.length > 0) return;
      cancelAllPolls();
      setError("");
      setNotFound(false);
      try {
        const msgs = await getChatSession(id);
        sessionRef.current = id;
        setSessionId(id);
        setTurns(
          msgs.map((m, i) => ({
            id: `h-${i}`,
            role: m.role,
            text: m.role === "user" ? m.text : undefined,
            block: m.role === "assistant" ? m.payload ?? undefined : undefined,
          }))
        );
        const last = [...msgs].reverse().find((m) => m.role === "assistant" && m.semantic_state);
        setSemanticState(last?.semantic_state ?? null);
      } catch (e) {
        setSessionId(null);
        setTurns([]);
        setSemanticState(null);
        if (e instanceof ApiError && e.status === 404) setNotFound(true);
        else setError(getApiErrorMessage(e, "Couldn't load that conversation."));
      }
    },
    [cancelAllPolls, turns.length]
  );

  const startNew = useCallback(() => {
    cancelAllPolls();
    sessionRef.current = null;
    setTurns([]);
    setError("");
    setNotFound(false);
    setSessionId(null);
    setSemanticState(null);
  }, [cancelAllPolls]);

  const handleAction = useCallback(async (req: AssistantActionRequest) => {
    const resultBlock = await runAssistantAction(req.endpoint, req.payload);
    setTurns((prev) => [...prev, { id: `act-${Date.now()}`, role: "assistant", block: resultBlock }]);
  }, []);

  /** Records open in a drawer; other pages route with a way back to this conversation. */
  const navigate = useCallback(
    (href: string) => {
      const m = RECORD_RE.exec(href);
      if (m && base === "/dashboard") {
        setRecord({ kind: m[1] === "students" ? "student" : "class", id: m[2], href });
        return;
      }
      const sid = sessionRef.current;
      if (sid && href.startsWith("/")) {
        const sep = href.includes("?") ? "&" : "?";
        router.push(`${href}${sep}from=${encodeURIComponent(`c/${sid}`)}`);
      } else {
        router.push(href);
      }
    },
    [router, base]
  );

  const value = useMemo<AssistantContextValue>(
    () => ({
      base,
      sessionId,
      turns,
      submitting,
      error,
      notFound,
      semanticState,
      pageContext,
      record,
      send,
      open,
      startNew,
      handleAction,
      navigate,
      setPageContext,
      closeRecord: () => setRecord(null),
      conversationHref,
    }),
    [base, sessionId, turns, submitting, error, notFound, semanticState, pageContext, record,
     send, open, startNew, handleAction, navigate, conversationHref]
  );

  return <AssistantContext.Provider value={value}>{children}</AssistantContext.Provider>;
}

export function useAssistant(): AssistantContextValue {
  const ctx = useContext(AssistantContext);
  if (!ctx) throw new Error("useAssistant must be used inside AssistantProvider");
  return ctx;
}

/** Optional variant for components that may render outside a provider (e.g. legacy pages). */
export function useAssistantOptional(): AssistantContextValue | null {
  return useContext(AssistantContext);
}
