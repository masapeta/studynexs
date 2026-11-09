"use client";

import { X } from "lucide-react";
import { useAssistant } from "./AssistantProvider";

function humanize(v: string): string {
  return v.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/** Visible carry-over context from the last turn; "Clear" starts a fresh conversation. */
export function ContextBar() {
  const { semanticState, pageContext, sessionId, startNew, setPageContext } = useAssistant();
  const chips: { key: string; label: string }[] = [];

  if (pageContext?.label) chips.push({ key: "page", label: `On: ${pageContext.label}` });
  if (semanticState?.domain) chips.push({ key: "domain", label: humanize(semanticState.domain) });
  for (const [k, v] of Object.entries(semanticState?.entities ?? {})) {
    if (v) chips.push({ key: `e-${k}`, label: String(v) });
  }
  if (semanticState?.subject) chips.push({ key: "subject", label: semanticState.subject });
  const time = semanticState?.temporal_time;
  if (typeof time === "string" && time) chips.push({ key: "time", label: humanize(time) });

  if (chips.length === 0) return null;
  return (
    <div className="sn-asst-context" role="group" aria-label="Conversation context">
      {chips.map((c) => (
        <span key={c.key} className="sn-ws-chip sn-asst-context__chip">
          {c.label}
        </span>
      ))}
      <button
        type="button"
        className="sn-asst-context__clear"
        onClick={() => {
          setPageContext(null);
          if (sessionId) startNew();
        }}
        aria-label="Clear context and start a new conversation"
      >
        <X size={14} aria-hidden /> Clear
      </button>
    </div>
  );
}
