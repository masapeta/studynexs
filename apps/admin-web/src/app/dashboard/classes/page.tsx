"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PersonMono } from "@/components/briefing/PersonMono";
import { formatClassLabel } from "@/lib/format";

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btnSm: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

export default function ClassesPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [years, setYears] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ grade: "", section: "", room_number: "", academic_year_id: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  function load() {
    setLoading(true);
    api("/api/v1/academic/classes")
      .then((r) => setClasses(r.items || r.data || []))
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    api("/api/v1/school/academic-years")
      .then((r) => {
        const items = r.data || r.items || [];
        setYears(items);
        const active = items.find((y: any) => y.is_active) || items[0];
        if (active) setForm((f) => ({ ...f, academic_year_id: active.id }));
      })
      .catch(() => {});
  }, []);

  async function addClass() {
    if (!form.grade.trim() || !form.section.trim() || !form.academic_year_id) {
      setError("Grade, section and academic year are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/academic/classes", {
        method: "POST",
        body: JSON.stringify({
          grade: form.grade,
          section: form.section,
          academic_year_id: form.academic_year_id,
          room_number: form.room_number || null,
        }),
      });
      setForm((f) => ({ ...f, grade: "", section: "", room_number: "" }));
      setShowAdd(false);
      load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add class"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="sn-page-toolbar">
        <h1 className="sn-page-title">Classes</h1>
        <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }} onClick={() => setShowAdd((v) => !v)}>
          {showAdd ? "Cancel" : "+ Add Class"}
        </button>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card sn-section-gap" style={{ padding: 18, display: "grid", gridTemplateColumns: "1.4fr 1fr 1fr 1.4fr auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Grade</label><input className="form-input" style={sel} value={form.grade} placeholder="Grade 5" onChange={(e) => setForm({ ...form, grade: e.target.value })} /></div>
          <div><label className="stat-label">Section</label><input className="form-input" style={sel} value={form.section} placeholder="A" onChange={(e) => setForm({ ...form, section: e.target.value })} /></div>
          <div><label className="stat-label">Room</label><input className="form-input" style={sel} value={form.room_number} onChange={(e) => setForm({ ...form, room_number: e.target.value })} /></div>
          <div>
            <label className="stat-label">Academic year</label>
            <AppSelect
              variant="field"
              value={form.academic_year_id}
              onChange={(v) => setForm({ ...form, academic_year_id: v })}
              aria-label="Academic year"
              placeholder="Select…"
              options={[
                { value: "", label: "Select…" },
                ...years.map((y) => ({
                  value: y.id,
                  label: `${y.year_label}${y.is_active ? " (active)" : ""}`,
                })),
              ]}
            />
          </div>
          <button className="btn btn-primary" style={btnSm} onClick={addClass} disabled={saving}>{saving ? "Adding…" : "Add"}</button>
        </div>
      )}

      <div className="dashboard-grid">
        {loading ? (
          <div className="card" style={{ gridColumn: "1/-1", textAlign: "center", padding: 40 }}>
            <div className="spinner" style={{ margin: "0 auto" }} />
          </div>
        ) : classes.length === 0 ? (
          <div className="card" style={{ gridColumn: "1/-1", textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
            No classes found. Create your first class.
          </div>
        ) : (
          classes.map((c: any) => (
            <div
              key={c.id}
              className="card"
              role="button"
              tabIndex={0}
              onClick={() => router.push(`/dashboard/classes/${c.id}`)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  router.push(`/dashboard/classes/${c.id}`);
                }
              }}
              style={{ cursor: "pointer" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                <PersonMono
                  name={c.class_incharge_name || "?"}
                  size={44}
                  title={
                    c.class_incharge_name
                      ? `Class teacher: ${c.class_incharge_name}`
                      : "No homeroom teacher assigned"
                  }
                />
                <div>
                  <div style={{ fontWeight: 700, fontSize: 16 }}>
                    {formatClassLabel(c.grade, c.section)}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    {c.student_count || 0} students
                    {c.class_incharge_name ? ` · ${c.class_incharge_name}` : ""}
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <div style={{ flex: 1, background: "var(--success-light)", borderRadius: "var(--radius-sm)", padding: "8px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Attendance</div>
                  <div style={{ fontWeight: 700, color: "var(--success)" }}>
                    {c.attendance_pct != null ? `${c.attendance_pct}%` : "—"}
                  </div>
                </div>
                <div style={{ flex: 1, background: "var(--primary-50)", borderRadius: "var(--radius-sm)", padding: "8px 12px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, color: "var(--text-muted)" }}>Avg Score</div>
                  <div style={{ fontWeight: 700, color: "var(--primary)" }}>
                    {c.avg_score != null ? `${c.avg_score}%` : "—"}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </>
  );
}
