"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

const sel: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btnSm: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

export default function StaffPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ full_name: "", mobile: "", email: "", role: "teacher" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { fetchStaff(); /* eslint-disable-next-line */ }, []);

  async function fetchStaff() {
    setLoading(true);
    try {
      const res = await api(`/api/v1/users?role=teacher&search=${search}&page_size=20`);
      setUsers(res.items || res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function addStaff() {
    if (!form.full_name.trim() || !form.mobile.trim()) {
      setError("Name and mobile are required.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/users", {
        method: "POST",
        body: JSON.stringify({ full_name: form.full_name, mobile: form.mobile, email: form.email || null, role: form.role }),
      });
      setForm({ full_name: "", mobile: "", email: "", role: "teacher" });
      setShowAdd(false);
      fetchStaff();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add staff"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Staff Management</h1>
        <div style={{ display: "flex", gap: 12 }}>
          <input
            className="form-input"
            placeholder="Search staff..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && fetchStaff()}
            style={{ width: 260 }}
          />
          <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }} onClick={() => setShowAdd((v) => !v)}>
            {showAdd ? "Cancel" : "+ Add Staff"}
          </button>
        </div>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 20, padding: 24, display: "grid", gridTemplateColumns: "1.5fr 1fr 1.5fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Full name</label><input className="form-input" style={sel} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
          <div><label className="stat-label">Mobile</label><input className="form-input" style={sel} value={form.mobile} onChange={(e) => setForm({ ...form, mobile: e.target.value })} /></div>
          <div><label className="stat-label">Email</label><input className="form-input" style={sel} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
          <div>
            <label className="stat-label">Role</label>
            <select className="form-input" style={sel} value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="teacher">Teacher</option>
              <option value="class_incharge">Class Incharge</option>
              <option value="operations">Operations</option>
            </select>
          </div>
          <button className="btn btn-primary" style={btnSm} onClick={addStaff} disabled={saving}>{saving ? "Adding…" : "Add"}</button>
        </div>
      )}

      <div className="data-table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
              <th>Email</th>
              <th>Mobile</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} style={{ textAlign: "center", padding: 40 }}>
                <div className="spinner" style={{ margin: "0 auto" }} />
              </td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                No staff found
              </td></tr>
            ) : (
              users.map((u: any) => (
                <tr key={u.id}>
                  <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                  <td style={{ textTransform: "capitalize" }}>{u.role?.replace("_", " ")}</td>
                  <td>{u.email || "—"}</td>
                  <td>{u.mobile || "—"}</td>
                  <td><span className={`status-dot ${u.is_active ? "green" : "red"}`} />{u.is_active ? "Active" : "Inactive"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
