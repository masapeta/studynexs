"use client";

import { useEffect, useMemo, useState } from "react";
import { BookOpen, BookPlus, Search, Upload } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";

type Book = {
  id: string;
  title: string;
  author?: string | null;
  total_copies: number;
  available_copies: number;
  issued_to?: string[];
};

export default function LibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ title: "", author: "", total_copies: 5 });
  const [saving, setSaving] = useState(false);

  function load(q?: string) {
    setLoading(true);
    const url = q?.trim()
      ? `/api/v1/ops/library/books?search=${encodeURIComponent(q.trim())}`
      : "/api/v1/ops/library/books";
    api<{ data: Book[] }>(url)
      .then((r) => setBooks(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load books")))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => {
    const total = books.reduce((n, b) => n + b.total_copies, 0);
    const borrowed = books.reduce(
      (n, b) => n + (b.total_copies - b.available_copies),
      0
    );
    const overdue = books.filter((b) => b.available_copies === 0 && (b.issued_to?.length || 0) > 0).length;
    return { titles: books.length, total, borrowed, overdue };
  }, [books]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return books;
    return books.filter(
      (b) =>
        b.title.toLowerCase().includes(q) ||
        (b.author || "").toLowerCase().includes(q)
    );
  }, [books, search]);

  async function addBook() {
    if (!form.title.trim()) {
      setError("Title is required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/ops/library/books", {
        method: "POST",
        body: JSON.stringify({
          title: form.title,
          author: form.author || null,
          total_copies: Number(form.total_copies) || 1,
        }),
      });
      setForm({ title: "", author: "", total_copies: 5 });
      setShowAdd(false);
      load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add book"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <PageShell title="Library" subtitle="Book catalog, borrowing, and returns management">
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      <div className="library-stats-grid">
        <div className="gw-card gw-card-pad library-stat">
          <div className="gw-muted">Total copies</div>
          <div className="library-stat-value">{stats.total}</div>
        </div>
        <div className="gw-card gw-card-pad library-stat">
          <div className="gw-muted">Titles in catalog</div>
          <div className="library-stat-value">{stats.titles}</div>
        </div>
        <div className="gw-card gw-card-pad library-stat">
          <div className="gw-muted">Currently borrowed</div>
          <div className="library-stat-value tone-brass">{stats.borrowed}</div>
        </div>
        <div className="gw-card gw-card-pad library-stat">
          <div className="gw-muted">Fully issued titles</div>
          <div className="library-stat-value tone-coral">{stats.overdue}</div>
        </div>
      </div>

      <div className="library-toolbar">
        <div className="topbar-search-trigger library-search">
          <Search size={16} />
          <input
            className="library-search-input"
            placeholder="Search title, author…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" className="btn btn-ghost gw-btn-sm" disabled title="Coming soon">
            <Upload size={14} /> Bulk import
          </button>
          <button type="button" className="btn btn-primary gw-btn-sm" onClick={() => setShowAdd((v) => !v)}>
            <BookPlus size={14} /> {showAdd ? "Cancel" : "Add book"}
          </button>
        </div>
      </div>

      {showAdd && (
        <div className="gw-card gw-card-pad" style={{ marginBottom: 20 }}>
          <div className="gw-expense-form" style={{ gridTemplateColumns: "2fr 1fr 100px auto" }}>
            <input
              className="form-input"
              placeholder="Title"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            <input
              className="form-input"
              placeholder="Author"
              value={form.author}
              onChange={(e) => setForm({ ...form, author: e.target.value })}
            />
            <input
              type="number"
              min={1}
              className="form-input"
              value={form.total_copies}
              onChange={(e) => setForm({ ...form, total_copies: Number(e.target.value) })}
            />
            <button type="button" className="btn btn-primary gw-btn-sm" onClick={addBook} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="gw-center">
          <div className="spinner" />
        </div>
      ) : filtered.length === 0 ? (
        <p className="gw-muted">No books match your search.</p>
      ) : (
        <div className="library-books-grid">
          {filtered.map((b) => {
            const borrowed = b.total_copies - b.available_copies;
            const pct = b.total_copies ? Math.round((b.available_copies / b.total_copies) * 100) : 0;
            return (
              <div key={b.id} className="gw-card library-book-card">
                <div className="library-book-cover">
                  <BookOpen size={28} />
                  <span className="library-book-cover-title">{b.title}</span>
                </div>
                <div className="library-book-body">
                  <div className="gw-list-title">{b.title}</div>
                  <div className="gw-list-meta">{b.author || "Unknown author"}</div>
                  <div className="library-book-stock">
                    <span>
                      Stock <strong>{b.available_copies}</strong>/{b.total_copies}
                    </span>
                    <span>Borrowed {borrowed}</span>
                  </div>
                  <div className="gw-progress-bar">
                    <div className="gw-progress-fill" style={{ width: `${pct}%` }} />
                  </div>
                  {(b.issued_to?.length || 0) > 0 && (
                    <div className="gw-list-meta" style={{ marginTop: 8 }}>
                      Issued: {b.issued_to!.join(", ")}
                    </div>
                  )}
                  <div className="library-book-actions">
                    <StatusBadge tone={b.available_copies > 0 ? "green" : "red"}>
                      {b.available_copies > 0 ? "Available" : "All out"}
                    </StatusBadge>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </PageShell>
  );
}
