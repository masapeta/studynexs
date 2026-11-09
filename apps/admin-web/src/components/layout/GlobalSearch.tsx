"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, MessageSquare, School, Search, UserCog } from "lucide-react";
import { api } from "@/lib/api";
import { listChatSessions } from "@/lib/assistant-client";
import type { UserPermissions } from "@/lib/permissions";

type Result = {
  id: string;
  label: string;
  meta?: string;
  href: string;
  kind: "student" | "staff" | "class" | "conversation";
};

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  permissions: UserPermissions | null;
  conversationHref: (id: string) => string;
};

type StudentRow = { id: string; student_name?: string; admission_no?: string; class_name?: string };
type StaffRow = { id: string; full_name: string; role?: string };

/**
 * Role-scoped ⌘K search (Rev 1 S1.8, Rev 2 E16). Each source is an existing endpoint that
 * enforces scope server-side; this only chooses which sources a role may ask, so no role fans
 * out to endpoints it can't use. Marks and mastery are never searched.
 */
export function TopBarSearch({ open, onOpenChange, permissions, conversationHref }: Props) {
  const router = useRouter();
  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(-1);

  const canSearchStaff = Boolean(permissions?.can_manage_staff);
  const isAdmin = Boolean(permissions?.is_admin);
  const inchargeKey = (permissions?.incharge_class_ids ?? []).join(",");
  const placeholder = canSearchStaff
    ? "Search students, staff, classes, chats…"
    : "Search classes, students, chats…";

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => inputRef.current?.focus(), 30);
    return () => clearTimeout(t);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) onOpenChange(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open, onOpenChange]);

  const search = useCallback(
    async (q: string) => {
      const term = q.trim();
      if (term.length < 2) {
        setResults([]);
        return;
      }
      setLoading(true);
      const enc = encodeURIComponent(term);
      const lower = term.toLowerCase();
      try {
        // The server scopes this to the school (admin) or every class the user is incharge of.
        // Subject teachers have no student-search endpoint in v1 — classes and chats only.
        const studentReq: Promise<StudentRow[]> =
          isAdmin || inchargeKey
            ? api<{ items?: StudentRow[] }>(`/api/v1/academic/students?search=${enc}&page_size=5`)
                .then((r) => r.items ?? [])
                .catch(() => [])
            : Promise.resolve([]);
        const [studentRows, staffRes, classesRes, sessions] = await Promise.all([
          studentReq,
          canSearchStaff
            ? api<{ items?: StaffRow[] }>(`/api/v1/users?search=${enc}&page_size=8`).catch(() => ({
                items: [] as StaffRow[],
              }))
            : Promise.resolve({ items: [] as StaffRow[] }),
          api<{ items?: { id: string; grade: string; section: string }[] }>(
            `/api/v1/academic/classes?page_size=100`
          ).catch(() => ({ items: [] })),
          listChatSessions().catch(() => []),
        ]);

        const students: Result[] = studentRows
          .slice(0, 5)
          .map((s) => ({
            id: s.id,
            label: s.student_name || s.admission_no || "Student",
            meta: [s.admission_no, s.class_name].filter(Boolean).join(" · "),
            href: `/dashboard/students/${s.id}`,
            kind: "student",
          }));
        const staff: Result[] = (staffRes.items ?? [])
          .filter((u) => u.role !== "parent" && u.role !== "student")
          .slice(0, 5)
          .map((u) => ({
            id: u.id,
            label: u.full_name,
            meta: u.role?.replace(/_/g, " "),
            href: "/dashboard/staff",
            kind: "staff",
          }));
        const classes: Result[] = (classesRes.items ?? [])
          .filter((c) =>
            `${c.grade} ${c.section} ${c.grade}-${c.section}`.toLowerCase().includes(lower)
          )
          .slice(0, 5)
          .map((c) => ({
            id: c.id,
            label: `${c.grade} - ${c.section}`,
            href: `/dashboard/classes/${c.id}`,
            kind: "class",
          }));
        const chats: Result[] = sessions
          .filter((s) => s.title.toLowerCase().includes(lower))
          .slice(0, 4)
          .map((s) => ({
            id: s.id,
            label: s.title,
            meta: "Conversation",
            href: conversationHref(s.id),
            kind: "conversation",
          }));
        setResults([...classes, ...students, ...staff, ...chats].slice(0, 14));
        setActive(-1);
      } finally {
        setLoading(false);
      }
    },
    [isAdmin, inchargeKey, canSearchStaff, conversationHref]
  );

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => void search(query), 300);
    return () => clearTimeout(t);
  }, [query, open, search]);

  const close = () => {
    setQuery("");
    setResults([]);
    setActive(-1);
    onOpenChange(false);
  };

  const go = (r: Result) => {
    close();
    router.push(r.href);
  };

  const iconFor = (kind: Result["kind"]) =>
    kind === "student"
      ? GraduationCap
      : kind === "staff"
        ? UserCog
        : kind === "conversation"
          ? MessageSquare
          : School;

  const trimmed = query.trim();
  const showDropdown = open && (loading || trimmed.length >= 2);

  if (!open) {
    return (
      <button
        type="button"
        className="topbar-search-trigger"
        aria-label="Open search"
        onClick={() => onOpenChange(true)}
      >
        <Search size={16} aria-hidden />
        <span className="topbar-search-placeholder">{placeholder}</span>
        <kbd className="topbar-search-kbd">⌘K</kbd>
      </button>
    );
  }

  return (
    <div ref={wrapRef} className="topbar-search-combobox">
      <div className="topbar-search-bar" role="search">
        <Search size={16} className="topbar-search-bar-icon" aria-hidden />
        <input
          ref={inputRef}
          type="text"
          className="topbar-search-input"
          placeholder={placeholder}
          value={query}
          maxLength={80}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") close();
            if (e.key === "ArrowDown") {
              e.preventDefault();
              setActive((i) => Math.min(i + 1, results.length - 1));
            }
            if (e.key === "ArrowUp") {
              e.preventDefault();
              setActive((i) => Math.max(i - 1, 0));
            }
            if (e.key === "Enter" && active >= 0 && results[active]) go(results[active]);
          }}
          role="combobox"
          aria-label={placeholder}
          aria-expanded={showDropdown}
          aria-controls="sn-search-results"
          aria-activedescendant={active >= 0 ? `sn-search-${active}` : undefined}
          autoComplete="off"
          spellCheck={false}
        />
        <kbd className="topbar-search-kbd">⌘K</kbd>
      </div>

      {showDropdown && (
        <div className="topbar-search-suggestions" role="listbox" id="sn-search-results">
          {loading && <p className="topbar-notif-empty">Searching…</p>}
          {!loading && trimmed.length >= 2 && results.length === 0 && (
            <p className="topbar-notif-empty">No results for &ldquo;{trimmed}&rdquo;</p>
          )}
          {results.map((r, i) => {
            const Icon = iconFor(r.kind);
            return (
              <button
                key={`${r.kind}-${r.id}`}
                id={`sn-search-${i}`}
                type="button"
                className="topbar-profile-item"
                role="option"
                aria-selected={i === active}
                style={i === active ? { background: "var(--accent-50)" } : undefined}
                onClick={() => go(r)}
              >
                <Icon size={16} aria-hidden />
                <span className="topbar-search-result-label">{r.label}</span>
                {r.meta && <span className="topbar-search-result-meta">{r.meta}</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
