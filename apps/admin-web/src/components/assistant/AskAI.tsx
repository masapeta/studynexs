"use client";

import { useEffect, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Sparkles, X } from "lucide-react";
import type { PageContext } from "@/lib/assistant-client";
import { useAssistantOptional } from "./AssistantProvider";
import { AssistantConversation } from "./AssistantConversation";

const SID_RE = /^c\/[0-9a-f-]{36}$/;

/** Header button: opens the assistant panel seeded with this page's context (a hint only). */
export function AskAIButton({ context }: { context: Omit<PageContext, "route"> }) {
  const assistant = useAssistantOptional();
  const pathname = usePathname();
  if (!assistant) return null;
  return (
    <button
      type="button"
      className="btn btn-ghost gw-btn-sm"
      onClick={() => {
        assistant.startNew();
        assistant.setPageContext({ ...context, route: pathname });
        window.dispatchEvent(new CustomEvent("sn-ask-ai-open"));
      }}
    >
      <Sparkles size={14} aria-hidden /> Ask AI
    </button>
  );
}

/** Side panel hosting the shared conversation; mounted once by the shell. */
export function AssistantPanel() {
  const assistant = useAssistantOptional();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener("sn-ask-ai-open", onOpen);
    return () => window.removeEventListener("sn-ask-ai-open", onOpen);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (!assistant || !open) return null;
  const ctx = assistant.pageContext;
  return (
    <aside className="sn-ws-panel sn-asst-panel" aria-label="Ask AI">
      <div className="sn-ws-panel__head">
        <strong className="sn-ws-panel__title">
          <Sparkles size={15} aria-hidden /> Ask AI{ctx?.label ? ` · ${ctx.label}` : ""}
        </strong>
        <button type="button" className="sn-ws-panel__close" onClick={() => setOpen(false)} aria-label="Close Ask AI">
          <X size={16} />
        </button>
      </div>
      <AssistantConversation
        compact
        placeholder={ctx?.label ? `Ask about ${ctx.label}…` : "Ask about this page…"}
        empty={
          <p className="sn-asst-muted">
            {ctx?.label
              ? `Questions here use ${ctx.label} as context. Your access is checked on every answer.`
              : "Ask a question about this page."}
          </p>
        }
      />
    </aside>
  );
}

/** "← Back to conversation" when a chat result routed here (?from=c/{id}). Never used for authz. */
export function BackToConversationChip() {
  const assistant = useAssistantOptional();
  const params = useSearchParams();
  const from = params.get("from");
  if (!assistant || !from || !SID_RE.test(from)) return null;
  return (
    <Link href={assistant.conversationHref(from.slice(2))} className="sn-asst-back" data-testid="back-to-conversation">
      <ArrowLeft size={14} aria-hidden /> Back to conversation
    </Link>
  );
}
