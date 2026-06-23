"use client";

import { useEffect, useState } from "react";
import { CalendarDays, MapPin } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";

type EventItem = {
  id: string;
  title: string;
  description?: string | null;
  event_date: string;
  event_time?: string | null;
  venue?: string | null;
};

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

function fmt(iso: string) {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

export default function EventsPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ title: "", event_date: new Date().toISOString().split("T")[0], venue: "", description: "" });
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    api("/api/v1/ops/events")
      .then((r) => setEvents(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load events")))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function addEvent() {
    if (!form.title.trim() || !form.event_date) { setError("Title and date are required."); return; }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/ops/events", {
        method: "POST",
        body: JSON.stringify({ title: form.title, event_date: form.event_date, venue: form.venue || null, description: form.description || null }),
      });
      setForm({ title: "", event_date: new Date().toISOString().split("T")[0], venue: "", description: "" });
      setShowAdd(false);
      load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to create event"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px", gap: 12, flexWrap: "wrap" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
          <CalendarDays size={20} /> Events
        </h1>
        <button className="btn btn-primary" style={btn} onClick={() => setShowAdd((v) => !v)}>
          {showAdd ? "Cancel" : "+ Create Event"}
        </button>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 24, padding: 24, display: "grid", gridTemplateColumns: "2fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Title</label><input className="form-input" style={sel} value={form.title} placeholder="Sports Day" onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><label className="stat-label">Date</label><input type="date" className="form-input" style={sel} value={form.event_date} onChange={(e) => setForm({ ...form, event_date: e.target.value })} /></div>
          <div><label className="stat-label">Venue</label><input className="form-input" style={sel} value={form.venue} onChange={(e) => setForm({ ...form, venue: e.target.value })} /></div>
          <button className="btn btn-primary" style={btn} onClick={addEvent} disabled={saving}>{saving ? "Saving…" : "Create"}</button>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>
      ) : events.length === 0 ? (
        <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>No events scheduled. Create one above.</div>
      ) : (
        <div className="dashboard-grid">
          {events.map((e) => (
            <div className="card" key={e.id}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                <div className="event-icon" style={{ background: "var(--info-light)" }}><CalendarDays size={18} color="var(--info)" /></div>
                <div style={{ fontWeight: 700 }}>{e.title}</div>
              </div>
              <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>{fmt(e.event_date)}{e.event_time ? ` · ${e.event_time}` : ""}</div>
              {e.venue && <div style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}><MapPin size={13} /> {e.venue}</div>}
              {e.description && <p style={{ fontSize: 13, marginTop: 8, color: "var(--text-secondary)" }}>{e.description}</p>}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
