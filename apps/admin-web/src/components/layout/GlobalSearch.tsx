"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, School, Search, UserCog } from "lucide-react";
import { api } from "@/lib/api";

type Result = {
  id: string;
  label: string;
  meta?: string;
  href: string;
  kind: "student" | "staff" | "class";
};

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function TopBarSearch({ open, onOpenChange }: Props) {
  const router = useRouter();
  const wrapRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setQuery("");
      setResults([]);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onOpenChange(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        onOpenChange(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open, onOpenChange]);

  const search = useCallback(async (q: string) => {
    const term = q.trim();
    if (term.length < 2) {
      setResults([]);
      return;
    }
    setLoading(true);
    try {
      const [studentsRes, staffRes, classesRes] = await Promise.all([
        api<{ items?: { id: string; student_name?: string; admission_no?: string }[] }>(
          `/api/v1/academic/students?search=${encodeURIComponent(term)}&page_size=5`
        ).catch(() => ({ items: [] })),
        api<{ items?: { id: string; full_name: string; role?: string }[] }>(
          `/api/v1/users?search=${encodeURIComponent(term)}&page_size=5`
        ).catch(() => ({ items: [] })),
        api<{ items?: { id: string; grade: string; section: string }[] }>(
          `/api/v1/academic/classes?page_size=50`
        ).catch(() => ({ items: [] })),
      ]);

      const studentItems = (studentsRes.items || []).map((s) => ({
        id: s.id,
        label: s.student_name || s.admission_no || "Student",
        meta: s.admission_no,
        href: `/dashboard/students`,
        kind: "student" as const,
      }));

      const staffItems = (staffRes.items || [])
        .filter((u) => u.role !== "parent" && u.role !== "student")
        .slice(0, 5)
        .map((u) => ({
          id: u.id,
          label: u.full_name,
          meta: u.role?.replace(/_/g, " "),
          href: `/dashboard/staff`,
          kind: "staff" as const,
        }));

      const lower = term.toLowerCase();
      const classItems = (classesRes.items || [])
        .filter((c) => `${c.grade} ${c.section}`.toLowerCase().includes(lower))
        .slice(0, 5)
        .map((c) => ({
          id: c.id,
          label: `${c.grade} ${c.section}`.trim(),
          href: `/dashboard/classes/${c.id}`,
          kind: "class" as const,
        }));

      setResults([...studentItems, ...staffItems, ...classItems].slice(0, 12));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => search(query), 250);
    return () => clearTimeout(t);
  }, [query, open, search]);

  const iconFor = (kind: Result["kind"]) => {
    if (kind === "student") return GraduationCap;
    if (kind === "staff") return UserCog;
    return School;
  };

  const trimmed = query.trim();
  const showDropdown = open && (loading || trimmed.length >= 2);

  if (!open) {
    return (
      <button
        type="button"
        className="topbar-search-trigger"
        onClick={() => onOpenChange(true)}
      >
        <Search size={16} aria-hidden />
        <span className="topbar-search-placeholder">Search students, teachers, classes…</span>
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
          placeholder="Search students, teachers, classes…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search students, teachers, classes"
          autoComplete="off"
          spellCheck={false}
        />
        <kbd className="topbar-search-kbd">⌘K</kbd>
      </div>

      {showDropdown && (
        <div className="topbar-search-suggestions" role="listbox">
          {loading && <p className="topbar-notif-empty">Searching…</p>}
          {!loading && trimmed.length >= 2 && results.length === 0 && (
            <p className="topbar-notif-empty">No results for &ldquo;{trimmed}&rdquo;</p>
          )}
          {results.map((r) => {
            const Icon = iconFor(r.kind);
            return (
              <button
                key={`${r.kind}-${r.id}`}
                type="button"
                className="topbar-profile-item"
                role="option"
                onClick={() => {
                  onOpenChange(false);
                  router.push(r.href);
                }}
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
