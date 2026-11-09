"use client";

import { useEffect } from "react";
import Link from "next/link";
import { MessageSquareOff, Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { EmptyState } from "@/components/ui/kit";
import { WORKSPACE_HERO, WORKSPACE_PROMPTS, roleToWorkspaceRole } from "@/lib/workspace-actions";
import { useAssistant } from "./AssistantProvider";
import { AssistantConversation } from "./AssistantConversation";

/** Full-page conversation. With `sessionId`, restores it (refresh-safe); 404 → not found. */
export function ChatPage({ sessionId }: { sessionId?: string }) {
  const { user } = useAuth();
  const { open, startNew, notFound, send, base, sessionId: current } = useAssistant();
  const wsRole = roleToWorkspaceRole(user?.role ?? "student");
  const hero = WORKSPACE_HERO[wsRole];
  const prompts = WORKSPACE_PROMPTS[wsRole];

  useEffect(() => {
    if (sessionId) void open(sessionId);
    else if (current) startNew();
    // Only react to the URL; `current` changes as the conversation progresses.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  if (sessionId && notFound) {
    return (
      <EmptyState
        icon={MessageSquareOff}
        title="Conversation not found"
        message="It may belong to another account, or the link is wrong."
        action={<Link href={`${base}/assistant`} className="btn btn-primary">Start a new chat</Link>}
      />
    );
  }

  return (
    <div className="sn-asst-page">
      <AssistantConversation
        empty={
          <>
            <div className="sn-ws-hero">
              <div className="sn-ws-hero__badge"><Sparkles size={26} aria-hidden /></div>
              <h1 className="sn-ws-hero__title">{hero.title}</h1>
              <p className="sn-ws-hero__sub">{hero.subtitle}</p>
            </div>
            <div className="sn-ws-chips">
              {prompts.map((p) => (
                <button key={p} type="button" className="sn-ws-chip" onClick={() => void send(p)}>
                  {p}
                </button>
              ))}
            </div>
          </>
        }
      />
    </div>
  );
}
