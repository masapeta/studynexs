"use client";

import { useAuth } from "@/lib/auth-context";
import { useCallback, useState, useRef, useEffect } from "react";
import { getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { ShortcutGrid, TEACHER_SHORTCUTS, ADMIN_SHORTCUTS } from "@/components/command/ShortcutGrid";
import { createWorkspaceTurn } from "@/lib/workspace-client";
import type { WorkspaceResponse } from "@/lib/workspace-types";
import {
  TeacherWorkspaceBlockRenderer,
} from "@/components/teaching/TeacherWorkspaceBlockRenderer";
import { Send, Sparkles } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const [text, setText] = useState("");
  const [response, setResponse] = useState<WorkspaceResponse | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.role === "admin" || user?.role === "super_admin";
  const shortcuts = isAdmin ? ADMIN_SHORTCUTS : TEACHER_SHORTCUTS;

  const handleShortcutClick = (intent: string) => {
    setText(intent);
    void submitTurn(intent);
  };

  async function submitTurn(nextText?: string) {
    const requestText = (nextText ?? text).trim();
    if (!requestText) return;

    setSubmitting(true);
    setError("");
    setResponse(null);

    try {
      const nextResponse = await createWorkspaceTurn({ mode: "read", text: requestText });
      setResponse(nextResponse);
      
      setTimeout(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 100);
      
    } catch (err) {
      setError(getApiErrorMessage(err, "StudyNexs Copilot could not complete that request."));
    } finally {
      setSubmitting(false);
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submitTurn();
    }
  };

  if (!user) return null;

  return (
    <PageShell
      title="Dashboard"
      subtitle=""
      action={<span className="sn-filter-pill px-3 py-1">AI-First Command Center</span>}
    >
      <div className="flex flex-col h-[calc(100vh-140px)] max-w-5xl mx-auto pb-6 relative">
        
        {/* Main Scrolling Workspace */}
        <div className="flex-1 overflow-y-auto pr-2 pb-32 space-y-8">
          
          <div className="text-center pt-8 pb-4">
             <div className="inline-flex items-center justify-center p-3 bg-mist/50 border border-line rounded-2xl mb-4">
                 <Sparkles className="text-accent" size={28} />
             </div>
             <h1 className="text-3xl font-bold tracking-tight text-primary mb-2">
                 How can StudyNexs help your academic day?
             </h1>
             <p className="text-muted text-sm max-w-lg mx-auto">
                 Ask about classes, attendance, assignments, exams, marks, fees, policies, or student progress.
             </p>
          </div>

          <ShortcutGrid shortcuts={shortcuts} onShortcutClick={handleShortcutClick} />

          {/* Active Conversation Stream */}
          {error && (
            <div className="p-4 bg-danger/10 border border-danger/20 rounded-xl text-danger text-sm">
                {error}
            </div>
          )}

          {response && (
             <div className="sn-workspace sn-workspace--primary p-6 rounded-2xl border border-line/80 shadow-[0_4px_24px_rgba(0,0,0,0.04)] animate-in slide-in-from-bottom-4 duration-300">
                <div className="mb-4 flex items-center justify-between border-b border-line pb-4">
                    <h3 className="font-bold text-lg text-ink">{response.message.title}</h3>
                    {response.verification?.status === "verified" && (
                        <div className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md border border-emerald-200">
                           Verified Source
                        </div>
                    )}
                </div>
                <p className="text-sm text-ink mb-6 leading-relaxed">{response.message.summary}</p>
                <div className="mt-4">
                    <TeacherWorkspaceBlockRenderer blocks={response.blocks} />
                </div>
                <div ref={scrollRef} />
             </div>
          )}
          
          {submitting && (
             <div className="flex items-center gap-3 p-6 text-muted text-sm animate-pulse">
                <Sparkles size={16} className="text-accent" />
                Orchestrating domain services...
             </div>
          )}
          
        </div>

        {/* Fixed Bottom Input Composer */}
        <div className="absolute bottom-0 left-0 right-0 pt-4 pb-2 bg-gradient-to-t from-page via-page to-transparent pr-2">
            <div className="relative sn-workspace sn-workspace--secondary p-2 rounded-2xl border border-line shadow-lg bg-surface/90 backdrop-blur-xl">
                 <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={submitting}
                    placeholder="Ask StudyNexs anything..."
                    className="w-full bg-transparent border-0 focus:ring-0 resize-none text-ink p-3 text-[15px] leading-relaxed placeholder:text-muted/60"
                    rows={2}
                 />
                 <div className="absolute bottom-3 right-3 flex items-center gap-2">
                     <button
                        type="button"
                        disabled={submitting || !text.trim()}
                        onClick={() => submitTurn()}
                        className="btn btn-accent flex items-center justify-center p-2 h-10 w-10 rounded-xl"
                     >
                        <Send size={18} strokeWidth={2.5} />
                     </button>
                 </div>
            </div>
        </div>

      </div>
    </PageShell>
  );
}
