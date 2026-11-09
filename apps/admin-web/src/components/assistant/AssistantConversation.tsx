"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { AssistantBlockView } from "@/components/workspace/AssistantBlockView";
import { useAssistant } from "./AssistantProvider";
import { ContextBar } from "./ContextBar";

/** Turn stream + composer, rendered from the shared provider (full page or side panel). */
export function AssistantConversation({
  empty,
  compact = false,
  placeholder = "Ask StudyNexs anything…",
}: {
  empty?: React.ReactNode;
  compact?: boolean;
  placeholder?: string;
}) {
  const { turns, submitting, error, send, handleAction, navigate } = useAssistant();
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, submitting]);

  const submit = () => {
    const value = text.trim();
    if (!value || submitting) return;
    setText("");
    void send(value);
  };

  return (
    <>
      <div className="sn-ws-scroll">
        <div className={compact ? "sn-asst-stream sn-asst-stream--compact" : "sn-ws-canvas"}>
          {turns.length === 0 ? (
            empty ?? null
          ) : (
            <div className="sn-asst-turns" aria-live="polite">
              {turns.map((turn) =>
                turn.role === "user" ? (
                  <div key={turn.id} className="sn-asst-user">
                    <div className="sn-asst-user__bubble">{turn.text}</div>
                  </div>
                ) : turn.block ? (
                  <AssistantBlockView
                    key={turn.id}
                    block={turn.block}
                    onSelect={(t) => void send(t)}
                    onAction={handleAction}
                    onNavigate={navigate}
                  />
                ) : null
              )}
            </div>
          )}

          {error ? (
            <div className="card sn-inline-alert sn-inline-alert--error" role="alert" style={{ margin: 0 }}>
              {error}
            </div>
          ) : null}

          {submitting ? (
            <div className="sn-asst-thinking" role="status">
              <Sparkles size={16} aria-hidden /> Thinking…
            </div>
          ) : null}
          <div ref={endRef} />
        </div>
      </div>

      <div className={compact ? "sn-asst-composer-wrap sn-asst-composer-wrap--compact" : "sn-ws-composer-wrap"}>
        <ContextBar />
        <div className="sn-ws-composer">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            disabled={submitting}
            rows={2}
            maxLength={1000}
            placeholder={placeholder}
            aria-label="Message StudyNexs"
          />
          <button
            type="button"
            className="sn-ws-composer__send"
            disabled={submitting || !text.trim()}
            onClick={submit}
            aria-label="Send message"
          >
            <Send size={18} strokeWidth={2.3} />
          </button>
        </div>
      </div>
    </>
  );
}
