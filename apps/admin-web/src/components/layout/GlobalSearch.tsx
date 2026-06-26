"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, School, Search, UserCog, X } from "lucide-react";
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
  onClose: () => void;
};

export function GlobalSearch({ open, onClose }: Props) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      setQuery("");
      setResults([]);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

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

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const iconFor = (kind: Result["kind"]) => {
    if (kind === "student") return GraduationCap;
    if (kind === "staff") return UserCog;
    return School;
  };

  return (
    <div className="topbar-search-overlay" onClick={onClose} role="presentation">
      <div className="topbar-search-modal" onClick={(e) => e.stopPropagation()}>
        <div className="topbar-search-input-row">
          <Search size={18} className="topbar-search-icon" />
          <input
            ref={inputRef}
            className="topbar-search-input"
            placeholder="Search students, teachers, classes..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd className="topbar-search-kbd">Esc</kbd>
          <button type="button" className="topbar-icon-btn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        <div className="topbar-search-results">
          {loading && <p className="topbar-search-hint">Searching…</p>}
          {!loading && query.length >= 2 && results.length === 0 && (
            <p className="topbar-search-hint">No matches for &ldquo;{query}&rdquo;</p>
          )}
          {!loading && query.length < 2 && (
            <p className="topbar-search-hint">Type at least 2 characters</p>
          )}
          {results.map((r) => {
            const Icon = iconFor(r.kind);
            return (
              <button
                key={`${r.kind}-${r.id}`}
                type="button"
                className="topbar-search-result"
                onClick={() => {
                  onClose();
                  router.push(r.href);
                }}
              >
                <Icon size={16} />
                <span className="topbar-search-result-label">{r.label}</span>
                {r.meta && <span className="topbar-search-result-meta">{r.meta}</span>}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
