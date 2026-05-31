"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
const DAY_LABEL: Record<string, string> = {
  monday: "Mon", tuesday: "Tue", wednesday: "Wed", thursday: "Thu", friday: "Fri", saturday: "Sat",
};

export default function TimetablePage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [slots, setSlots] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({
    day_of_week: "monday", period_number: 1, subject_id: "", teacher_id: "",
    start_time: "09:00", end_time: "09:45",
  });

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = r.items || r.data || [];
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => console.error(e));
    api("/api/v1/users?role=teacher&page_size=100")
      .then((r) => {
        const items = r.items || r.data || [];
        setTeachers(items);
        setForm((f) => ({ ...f, teacher_id: items[0]?.id || "" }));
      })
      .catch((e) => console.error(e));
  }, []);

  useEffect(() => {
    if (!classId) return;
    api(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((r) => {
        const items = r.items || r.data || (Array.isArray(r) ? r : []);
        setSubjects(items);
        setForm((f) => ({ ...f, subject_id: items[0]?.id || "" }));
      })
      .catch((e) => console.error(e));
    loadSlots();
  }, [classId]);

  function loadSlots() {
    setLoading(true);
    api(`/api/v1/timetable/class/${classId}`)
      .then((r) => setSlots(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load timetable")))
      .finally(() => setLoading(false));
  }

  async function addSlot() {
    if (!form.subject_id || !form.teacher_id) {
      setError("Pick a subject and a teacher.");
      return;
    }
    setAdding(true);
    setError("");
    try {
      await api("/api/v1/timetable", {
        method: "POST",
        body: JSON.stringify({ class_id: classId, ...form, period_number: Number(form.period_number) }),
      });
      loadSlots();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add slot (a slot may already exist for that day/period)."));
    } finally {
      setAdding(false);
    }
  }

  async function deleteSlot(id: string) {
    try {
      await api(`/api/v1/timetable/${id}`, { method: "DELETE" });
      loadSlots();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to delete slot"));
    }
  }

  const subjName = (id: string) => subjects.find((s) => s.id === id)?.name || "—";
  const teachName = (id: string) => teachers.find((t) => t.id === id)?.full_name || "—";

  const maxPeriod = Math.max(8, ...slots.map((s) => s.period_number || 0));
  const periods = Array.from({ length: maxPeriod }, (_, i) => i + 1);
  const slotMap: Record<string, any> = {};
  slots.forEach((s) => (slotMap[`${s.day_of_week}-${s.period_number}`] = s));

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px 24px" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Timetable</h1>
        <select className="form-input" value={classId} onChange={(e) => setClassId(e.target.value)} style={sel}>
          {classes.map((c) => <option key={c.id} value={c.id}>{c.grade} - {c.section}</option>)}
        </select>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {/* Add slot */}
      <div className="card" style={{ marginBottom: 24, padding: 20, display: "grid", gridTemplateColumns: "repeat(6, 1fr) auto", gap: 10, alignItems: "end" }}>
        <div>
          <label className="stat-label">Day</label>
          <select className="form-input" style={sel} value={form.day_of_week} onChange={(e) => setForm({ ...form, day_of_week: e.target.value })}>
            {DAYS.map((d) => <option key={d} value={d}>{DAY_LABEL[d]}</option>)}
          </select>
        </div>
        <div>
          <label className="stat-label">Period</label>
          <input type="number" min={1} className="form-input" style={sel} value={form.period_number} onChange={(e) => setForm({ ...form, period_number: Number(e.target.value) })} />
        </div>
        <div>
          <label className="stat-label">Subject</label>
          <select className="form-input" style={sel} value={form.subject_id} onChange={(e) => setForm({ ...form, subject_id: e.target.value })}>
            {subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div>
          <label className="stat-label">Teacher</label>
          <select className="form-input" style={sel} value={form.teacher_id} onChange={(e) => setForm({ ...form, teacher_id: e.target.value })}>
            {teachers.map((t) => <option key={t.id} value={t.id}>{t.full_name}</option>)}
          </select>
        </div>
        <div>
          <label className="stat-label">Start</label>
          <input type="time" className="form-input" style={sel} value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
        </div>
        <div>
          <label className="stat-label">End</label>
          <input type="time" className="form-input" style={sel} value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
        </div>
        <button className="btn btn-primary" style={btn} onClick={addSlot} disabled={adding}>
          {adding ? "Adding…" : "+ Add"}
        </button>
      </div>

      {/* Weekly grid */}
      <div className="card" style={{ padding: 0, overflow: "auto" }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: "center" }}><div className="spinner" style={{ margin: "0 auto" }} /></div>
        ) : (
          <table className="data-table" style={{ minWidth: 720 }}>
            <thead>
              <tr>
                <th style={{ width: 70 }}>Period</th>
                {DAYS.map((d) => <th key={d}>{DAY_LABEL[d]}</th>)}
              </tr>
            </thead>
            <tbody>
              {periods.map((p) => (
                <tr key={p}>
                  <td style={{ fontWeight: 700 }}>{p}</td>
                  {DAYS.map((d) => {
                    const s = slotMap[`${d}-${p}`];
                    return (
                      <td key={d} style={{ verticalAlign: "top" }}>
                        {s ? (
                          <div style={{ background: "var(--bg)", borderRadius: "var(--radius-sm)", padding: "6px 8px", position: "relative" }}>
                            <div style={{ fontWeight: 600, fontSize: 13 }}>{subjName(s.subject_id)}</div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{teachName(s.teacher_id)}</div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{s.start_time}–{s.end_time}</div>
                            <button onClick={() => deleteSlot(s.id)} title="Remove"
                              style={{ position: "absolute", top: 4, right: 4, border: "none", background: "none", cursor: "pointer", color: "var(--danger)", fontSize: 12 }}>✕</button>
                          </div>
                        ) : (
                          <span style={{ color: "var(--text-muted)" }}>—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

const sel: React.CSSProperties = { width: "100%", padding: "8px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
