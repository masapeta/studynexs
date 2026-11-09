"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Archive, ArchiveRestore, MessageSquare, Pencil, Search, X } from "lucide-react";
import { getApiErrorMessage } from "@/lib/api";
import { listChatSessions, updateChatSession, type ChatSessionSummary } from "@/lib/assistant-client";
import { useAssistant } from "./AssistantProvider";

function groupLabel(iso: string | null): string {
  if (!iso) return "Older";
  const d = new Date(iso);
  const today = new Date();
  const startOf = (x: Date) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const days = Math.round((startOf(today) - startOf(d)) / 86_400_000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return "Previous 7 days";
  return "Older";
}

const GROUP_ORDER = ["Today", "Yesterday", "Previous 7 days", "Older"];

/** Conversation history drawer: search, date groups, rename, archive / restore (never delete). */
export function ConversationList({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { conversationHref, sessionId, startNew } = useAssistant();
  const [archived, setArchived] = useState(false);
  const [items, setItems] = useState<ChatSessionSummary[] | null>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    let alive = true;
    listChatSessions({ archived })
      .then((rows) => {
        if (!alive) return;
        setItems(rows);
        setError("");
      })
      .catch((e) => {
        if (!alive) return;
        setItems([]);
        setError(getApiErrorMessage(e, "Couldn't load conversations."));
      });
    return () => {
      alive = false;
      setItems(null);
    };
  }, [open, archived]);

  useEffect(() => {
    if (!open) return;
    setTimeout(() => closeRef.current?.focus(), 20);
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const grouped = useMemo(() => {
    const q = query.trim().toLowerCase();
    const map = new Map<string, ChatSessionSummary[]>();
    for (const s of items ?? []) {
      if (q && !s.title.toLowerCase().includes(q)) continue;
      const g = groupLabel(s.updated_at);
      map.set(g, [...(map.get(g) ?? []), s]);
    }
    return GROUP_ORDER.filter((g) => map.has(g)).map((g) => [g, map.get(g)!] as const);
  }, [items, query]);

  async function rename(id: string) {
    const title = draft.trim();
    if (!title) return;
    setBusy(id);
    try {
      const updated = await updateChatSession(id, { title });
      setItems((prev) => prev?.map((s) => (s.id === id ? updated : s)) ?? prev);
      setEditing(null);
    } catch (e) {
      setError(getApiErrorMessage(e, "Rename failed."));
    } finally {
      setBusy(null);
    }
  }

  async function toggleArchive(s: ChatSessionSummary) {
    setBusy(s.id);
    try {
      await updateChatSession(s.id, { archived: !archived });
      setItems((prev) => prev?.filter((x) => x.id !== s.id) ?? prev);
      if (!archived && s.id === sessionId) startNew();
    } catch (e) {
      setError(getApiErrorMessage(e, "That change couldn't be saved."));
    } finally {
      setBusy(null);
    }
  }

  if (!open) return null;
  return (
    <div role="dialog" aria-modal="true" aria-label="Conversations" className="sn-asst-drawer">
      <div className="sn-asst-drawer__scrim" onClick={onClose} aria-hidden />
      <div className="sn-asst-drawer__sheet">
        <div className="sn-ws-panel__head">
          <strong className="sn-ws-panel__title">{archived ? "Archived conversations" : "Conversations"}</strong>
          <button ref={closeRef} type="button" className="sn-ws-panel__close" onClick={onClose}
                  aria-label="Close conversations">
            <X size={16} />
          </button>
        </div>
        <div className="sn-asst-drawer__tools">
          <label className="sn-asst-search">
            <Search size={14} aria-hidden />
            <input value={query} onChange={(e) => setQuery(e.target.value)}
                   placeholder="Search titles" aria-label="Search conversations" />
          </label>
          <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => setArchived((a) => !a)}
                  aria-pressed={archived}>
            {archived ? "Show active" : "Show archived"}
          </button>
        </div>
        <div className="sn-ws-panel__body">
          {error ? <div className="sn-inline-alert sn-inline-alert--error" role="alert">{error}</div> : null}
          {items === null ? (
            <div className="spinner" style={{ margin: "24px auto" }} aria-label="Loading conversations" />
          ) : grouped.length === 0 ? (
            <p className="sn-asst-muted">
              {query ? `No conversations match “${query}”.` : archived ? "Nothing archived." : "No conversations yet."}
            </p>
          ) : (
            grouped.map(([label, rows]) => (
              <section key={label}>
                <div className="sn-ws-panel__section-label">{label}</div>
                <ul className="sn-asst-list">
                  {rows.map((s) => (
                    <li key={s.id} className="sn-asst-list__row">
                      {editing === s.id ? (
                        <form className="sn-asst-list__rename"
                              onSubmit={(e) => { e.preventDefault(); void rename(s.id); }}>
                          <input value={draft} maxLength={200} autoFocus aria-label="Conversation title"
                                 onChange={(e) => setDraft(e.target.value)} />
                          <button type="submit" className="btn btn-primary gw-btn-sm" disabled={busy === s.id}>Save</button>
                          <button type="button" className="btn btn-ghost gw-btn-sm" onClick={() => setEditing(null)}>Cancel</button>
                        </form>
                      ) : (
                        <>
                          <Link href={conversationHref(s.id)} className="sn-asst-list__link" onClick={onClose}
                                aria-current={s.id === sessionId ? "page" : undefined}>
                            <MessageSquare size={15} aria-hidden />
                            <span>{s.title}</span>
                          </Link>
                          <button type="button" className="sn-ws-panel__close" title="Rename"
                                  aria-label={`Rename ${s.title}`}
                                  onClick={() => { setEditing(s.id); setDraft(s.title); }}>
                            <Pencil size={14} />
                          </button>
                          <button type="button" className="sn-ws-panel__close" disabled={busy === s.id}
                                  title={archived ? "Restore" : "Archive"}
                                  aria-label={`${archived ? "Restore" : "Archive"} ${s.title}`}
                                  onClick={() => void toggleArchive(s)}>
                            {archived ? <ArchiveRestore size={14} /> : <Archive size={14} />}
                          </button>
                        </>
                      )}
                    </li>
                  ))}
                </ul>
              </section>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
