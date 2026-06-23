"use client";

import { useEffect, useState } from "react";
import { BookOpen, Search } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";

type Book = {
  id: string;
  title: string;
  author?: string | null;
  isbn?: string | null;
  category?: string | null;
  total_copies: number;
  available_copies: number;
};

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

export default function LibraryPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ title: "", author: "", isbn: "", category: "", total_copies: 1 });
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    api(`/api/v1/ops/library/books${search ? `?search=${encodeURIComponent(search)}` : ""}`)
      .then((r) => setBooks(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load books")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); /* eslint-disable-next-line */ }, []);

  async function addBook() {
    if (!form.title.trim()) { setError("Title is required."); return; }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/ops/library/books", {
        method: "POST",
        body: JSON.stringify({ ...form, total_copies: Number(form.total_copies) }),
      });
      setForm({ title: "", author: "", isbn: "", category: "", total_copies: 1 });
      setShowAdd(false);
      load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add book"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          <BookOpen size={20} /> Library
        </h1>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ position: "relative" }}>
            <Search size={15} style={{ position: "absolute", left: 10, top: 9, color: "var(--text-muted)" }} />
            <input
              className="form-input"
              placeholder="Search title/author"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && load()}
              style={{ padding: "7px 12px 7px 30px", borderRadius: "var(--radius-full)", border: "1px solid var(--border)" }}
            />
          </div>
          <button className="btn btn-primary" style={btn} onClick={() => setShowAdd((v) => !v)}>
            {showAdd ? "Cancel" : "+ Add Book"}
          </button>
        </div>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 24, padding: 24, display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Title</label><input className="form-input" style={sel} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><label className="stat-label">Author</label><input className="form-input" style={sel} value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} /></div>
          <div><label className="stat-label">Category</label><input className="form-input" style={sel} value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} /></div>
          <div><label className="stat-label">Copies</label><input type="number" min={1} className="form-input" style={sel} value={form.total_copies} onChange={(e) => setForm({ ...form, total_copies: Number(e.target.value) })} /></div>
          <button className="btn btn-primary" style={btn} onClick={addBook} disabled={saving}>{saving ? "Saving…" : "Add"}</button>
        </div>
      )}

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="data-table">
          <thead><tr><th>Title</th><th>Author</th><th>Category</th><th style={{ textAlign: "right" }}>Available</th></tr></thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} style={{ textAlign: "center", padding: 40 }}><div className="spinner" style={{ margin: "0 auto" }} /></td></tr>
            ) : books.length === 0 ? (
              <tr><td colSpan={4} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>No books yet. Add one above.</td></tr>
            ) : books.map((b) => (
              <tr key={b.id}>
                <td style={{ fontWeight: 600 }}>{b.title}</td>
                <td>{b.author || "—"}</td>
                <td>{b.category || "—"}</td>
                <td style={{ textAlign: "right" }}>
                  <span className={`badge ${b.available_copies > 0 ? "badge-success" : "badge-danger"}`}>
                    {b.available_copies} / {b.total_copies}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
