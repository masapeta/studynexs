"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel, sortClasses } from "@/lib/format";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
const DAY_LABEL: Record<string, string> = {
  monday: "Mon", tuesday: "Tue", wednesday: "Wed", thursday: "Thu", friday: "Fri", saturday: "Sat",
};

export default function TimetablePage() {
  const { permissions } = useAuth();
  const canEdit = permissions?.can_edit_timetable ?? false;
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
        setClasses(sortClasses<any>(items));
        if (items[0]) setClassId(items[0].id);
      })
      .catch((e) => console.error(e));
    if (canEdit) {
      api("/api/v1/users?role=teacher&page_size=100")
        .then((r) => {
          const items = r.items || r.data || [];
          setTeachers(items);
          setForm((f) => ({ ...f, teacher_id: items[0]?.id || "" }));
        })
        .catch((e) => console.error(e));
    }
  }, [canEdit]);

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

  const subjName = (id: string, slot?: { subject_name?: string | null }) =>
    slot?.subject_name || subjects.find((s) => s.id === id)?.name || "—";
  const teachName = (id: string, slot?: { teacher_name?: string | null }) =>
    slot?.teacher_name || teachers.find((t) => t.id === id)?.full_name || "—";

  const maxPeriod = Math.max(8, ...slots.map((s) => s.period_number || 0));
  const periods = Array.from({ length: maxPeriod }, (_, i) => i + 1);
  const slotMap: Record<string, any> = {};
  slots.forEach((s) => (slotMap[`${s.day_of_week}-${s.period_number}`] = s));

  return (
    <>
      <PageHeaderCard title="Timetable">
        <AppSelect
          variant="pill"
          value={classId}
          onChange={setClassId}
          aria-label="Select class"
          options={classes.map((c) => ({
            value: c.id,
            label: formatClassLabel(c.grade, c.section),
          }))}
        />
      </PageHeaderCard>

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}

      {canEdit && (
      <div className="card sn-content-card sn-form-row sn-form-row--timetable">
        <div>
          <label className="stat-label">Day</label>
          <AppSelect
            variant="field"
            value={form.day_of_week}
            onChange={(v) => setForm({ ...form, day_of_week: v })}
            aria-label="Day"
            options={DAYS.map((d) => ({ value: d, label: DAY_LABEL[d] }))}
          />
        </div>
        <div>
          <label className="stat-label">Period</label>
          <input type="number" min={1} className="form-input sn-inline-field" value={form.period_number} onChange={(e) => setForm({ ...form, period_number: Number(e.target.value) })} />
        </div>
        <div>
          <label className="stat-label">Subject</label>
          <AppSelect
            variant="field"
            value={form.subject_id}
            onChange={(v) => setForm({ ...form, subject_id: v })}
            aria-label="Subject"
            options={subjects.map((s) => ({ value: s.id, label: s.name }))}
          />
        </div>
        <div>
          <label className="stat-label">Teacher</label>
          <AppSelect
            variant="field"
            value={form.teacher_id}
            onChange={(v) => setForm({ ...form, teacher_id: v })}
            aria-label="Teacher"
            options={teachers.map((t) => ({ value: t.id, label: t.full_name }))}
          />
        </div>
        <div>
          <label className="stat-label">Start</label>
          <input type="time" className="form-input sn-inline-field" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
        </div>
        <div>
          <label className="stat-label">End</label>
          <input type="time" className="form-input sn-inline-field" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
        </div>
        <button className="btn btn-primary" style={btn} onClick={addSlot} disabled={adding}>
          {adding ? "Adding…" : "+ Add"}
        </button>
      </div>
      )}

      {!canEdit && (
        <div className="card sn-info-banner">
          View-only timetable. Only the principal and class incharges can add or edit slots.
        </div>
      )}

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
                            <div style={{ fontWeight: 600, fontSize: 13 }}>{subjName(s.subject_id, s)}</div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{teachName(s.teacher_id, s)}</div>
                            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>{s.start_time}–{s.end_time}</div>
                            {canEdit && (
                            <button onClick={() => deleteSlot(s.id)} title="Remove"
                              style={{ position: "absolute", top: 4, right: 4, border: "none", background: "none", cursor: "pointer", color: "var(--danger)", fontSize: 12 }}>✕</button>
                            )}
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

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };
