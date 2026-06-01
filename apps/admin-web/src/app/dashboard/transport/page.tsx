"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { Bus, Plus, MapPin } from "lucide-react";

const inp: React.CSSProperties = { marginTop: 4 };

export default function TransportPage() {
  const [routes, setRoutes] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [students, setStudents] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ route_name: "", vehicle_number: "", driver_name: "", driver_contact: "", stops: "" });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadRoutes(); }, []);

  function loadRoutes() {
    api("/api/v1/ops/transport/routes")
      .then((r) => setRoutes(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load routes")));
  }

  async function openRoute(route: any) {
    setSelected(route);
    try {
      const r = await api(`/api/v1/ops/transport/routes/${route.id}/students`);
      setStudents(r.data || []);
    } catch {
      setStudents([]);
    }
  }

  async function addRoute() {
    if (!form.route_name) { setError("Route name is required."); return; }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/ops/transport/routes", {
        method: "POST",
        body: JSON.stringify({ ...form, stops: form.stops.split(",").map((s) => s.trim()).filter(Boolean) }),
      });
      setForm({ route_name: "", vehicle_number: "", driver_name: "", driver_contact: "", stops: "" });
      setShowAdd(false);
      loadRoutes();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add route"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Transport</h1>
          <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: 13 }}>Bus routes and student assignments.</p>
        </div>
        <button className="btn btn-primary" style={{ width: "auto", padding: "8px 18px" }} onClick={() => setShowAdd((v) => !v)}>
          <Plus size={16} /> Add Route
        </button>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 24, padding: 24 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, marginTop: 0, marginBottom: 16 }}>New Route</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div><label className="stat-label">Route name</label><input className="form-input" style={inp} value={form.route_name} onChange={(e) => setForm({ ...form, route_name: e.target.value })} placeholder="Route 4 — Gachibowli" /></div>
            <div><label className="stat-label">Vehicle number</label><input className="form-input" style={inp} value={form.vehicle_number} onChange={(e) => setForm({ ...form, vehicle_number: e.target.value })} placeholder="TS09 GH 3456" /></div>
            <div><label className="stat-label">Driver name</label><input className="form-input" style={inp} value={form.driver_name} onChange={(e) => setForm({ ...form, driver_name: e.target.value })} /></div>
            <div><label className="stat-label">Driver contact</label><input className="form-input" style={inp} value={form.driver_contact} onChange={(e) => setForm({ ...form, driver_contact: e.target.value })} /></div>
            <div style={{ gridColumn: "1 / -1" }}><label className="stat-label">Stops (comma-separated)</label><input className="form-input" style={inp} value={form.stops} onChange={(e) => setForm({ ...form, stops: e.target.value })} placeholder="Gachibowli, Kondapur, Madhapur" /></div>
          </div>
          <button className="btn btn-primary" style={{ width: "auto", padding: "8px 20px", marginTop: 16 }} onClick={addRoute} disabled={saving}>
            {saving ? "Saving…" : "Create Route"}
          </button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16, marginBottom: 24 }}>
        {routes.map((rt) => (
          <div key={rt.id} className="card" style={{ padding: 20, cursor: "pointer", borderColor: selected?.id === rt.id ? "var(--accent)" : undefined }} onClick={() => openRoute(rt)}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <div className="stat-icon-container icon-blue"><Bus size={20} /></div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700 }}>{rt.route_name}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{rt.vehicle_number || "—"}</div>
              </div>
              <span className="badge badge-info">{rt.student_count} students</span>
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 10 }}>
              Driver: {rt.driver_name || "—"}{rt.driver_contact ? ` · ${rt.driver_contact}` : ""}
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {(rt.stops || []).map((s: string, i: number) => (
                <span key={i} style={{ fontSize: 11, padding: "3px 8px", background: "var(--bg)", borderRadius: "var(--radius-full)", display: "inline-flex", alignItems: "center", gap: 4 }}>
                  <MapPin size={11} />{s}
                </span>
              ))}
            </div>
          </div>
        ))}
        {routes.length === 0 && <div style={{ color: "var(--text-muted)", fontSize: 14 }}>No routes yet. Add one above.</div>}
      </div>

      {selected && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 22px", fontWeight: 700, borderBottom: "1px solid var(--border-light)" }}>
            {selected.route_name} — {students.length} students
          </div>
          {students.length === 0 ? (
            <div style={{ padding: 24, color: "var(--text-muted)", fontSize: 14 }}>No students assigned to this route.</div>
          ) : (
            <table className="data-table">
              <thead><tr><th>Admission No</th><th>Student</th><th>Boarding Stop</th></tr></thead>
              <tbody>
                {students.map((s: any) => (
                  <tr key={s.student_id}>
                    <td style={{ fontWeight: 600 }}>{s.admission_no}</td>
                    <td>{s.name}</td>
                    <td>{s.boarding_stop || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </>
  );
}
