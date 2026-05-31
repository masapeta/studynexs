"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

export default function SettingsPage() {
  const [profile, setProfile] = useState<any>({ name: "", board: "", contact_email: "", contact_phone: "", address: {} });
  const [years, setYears] = useState<any[]>([]);
  const [savingProfile, setSavingProfile] = useState(false);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [newYear, setNewYear] = useState({ year_label: "", start_date: "", end_date: "", is_active: false });
  const [addingYear, setAddingYear] = useState(false);

  useEffect(() => {
    api("/api/v1/school/profile")
      .then((r) => setProfile({ ...(r.data || {}), address: r.data?.address || {} }))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load school profile")));
    loadYears();
  }, []);

  function loadYears() {
    api("/api/v1/school/academic-years")
      .then((r) => setYears(r.data || []))
      .catch(() => {});
  }

  async function saveProfile() {
    setSavingProfile(true);
    setError("");
    setMsg("");
    try {
      const r = await api("/api/v1/school/profile", {
        method: "PATCH",
        body: JSON.stringify({
          name: profile.name,
          board: profile.board,
          contact_email: profile.contact_email,
          contact_phone: profile.contact_phone,
          address: profile.address,
        }),
      });
      setProfile({ ...(r.data || profile), address: r.data?.address || {} });
      setMsg("School profile saved.");
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save profile"));
    } finally {
      setSavingProfile(false);
    }
  }

  async function addYear() {
    if (!newYear.year_label || !newYear.start_date || !newYear.end_date) {
      setError("Fill the academic year label and dates.");
      return;
    }
    setAddingYear(true);
    setError("");
    try {
      await api("/api/v1/school/academic-years", { method: "POST", body: JSON.stringify(newYear) });
      setNewYear({ year_label: "", start_date: "", end_date: "", is_active: false });
      loadYears();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add academic year"));
    } finally {
      setAddingYear(false);
    }
  }

  const addr = profile.address || {};

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, padding: "16px 24px" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>School Settings</h1>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}
      {msg && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--success)" }}>{msg}</div>}

      {/* School profile */}
      <div className="card" style={{ marginBottom: 24, padding: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, marginTop: 0, marginBottom: 16 }}>School Profile</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div><label className="stat-label">School name</label>
            <input className="form-input" style={inp} value={profile.name || ""} onChange={(e) => setProfile({ ...profile, name: e.target.value })} /></div>
          <div><label className="stat-label">Board</label>
            <input className="form-input" style={inp} value={profile.board || ""} onChange={(e) => setProfile({ ...profile, board: e.target.value })} /></div>
          <div><label className="stat-label">Contact email</label>
            <input className="form-input" style={inp} value={profile.contact_email || ""} onChange={(e) => setProfile({ ...profile, contact_email: e.target.value })} /></div>
          <div><label className="stat-label">Contact phone</label>
            <input className="form-input" style={inp} value={profile.contact_phone || ""} onChange={(e) => setProfile({ ...profile, contact_phone: e.target.value })} /></div>
          <div><label className="stat-label">City</label>
            <input className="form-input" style={inp} value={addr.city || ""} onChange={(e) => setProfile({ ...profile, address: { ...addr, city: e.target.value } })} /></div>
          <div><label className="stat-label">State</label>
            <input className="form-input" style={inp} value={addr.state || ""} onChange={(e) => setProfile({ ...profile, address: { ...addr, state: e.target.value } })} /></div>
        </div>
        <div style={{ marginTop: 16 }}>
          <button className="btn btn-primary" style={btn} onClick={saveProfile} disabled={savingProfile}>
            {savingProfile ? "Saving…" : "Save Profile"}
          </button>
        </div>
      </div>

      {/* Academic years */}
      <div className="card" style={{ padding: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, marginTop: 0, marginBottom: 16 }}>Academic Years</h2>
        <table className="data-table" style={{ marginBottom: 16 }}>
          <thead><tr><th>Year</th><th>Start</th><th>End</th><th>Active</th></tr></thead>
          <tbody>
            {years.length === 0 ? (
              <tr><td colSpan={4} style={{ textAlign: "center", padding: 24, color: "var(--text-muted)" }}>No academic years yet.</td></tr>
            ) : years.map((y) => (
              <tr key={y.id}>
                <td style={{ fontWeight: 600 }}>{y.year_label}</td>
                <td>{y.start_date}</td>
                <td>{y.end_date}</td>
                <td>{y.is_active ? <span className="status-dot green" /> : null}{y.is_active ? "Active" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr auto auto", gap: 12, alignItems: "end" }}>
          <div><label className="stat-label">Label</label>
            <input className="form-input" style={inp} placeholder="2027-2028" value={newYear.year_label} onChange={(e) => setNewYear({ ...newYear, year_label: e.target.value })} /></div>
          <div><label className="stat-label">Start</label>
            <input type="date" className="form-input" style={inp} value={newYear.start_date} onChange={(e) => setNewYear({ ...newYear, start_date: e.target.value })} /></div>
          <div><label className="stat-label">End</label>
            <input type="date" className="form-input" style={inp} value={newYear.end_date} onChange={(e) => setNewYear({ ...newYear, end_date: e.target.value })} /></div>
          <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, paddingBottom: 8 }}>
            <input type="checkbox" checked={newYear.is_active} onChange={(e) => setNewYear({ ...newYear, is_active: e.target.checked })} /> Active
          </label>
          <button className="btn btn-primary" style={btn} onClick={addYear} disabled={addingYear}>
            {addingYear ? "Adding…" : "+ Add"}
          </button>
        </div>
      </div>
    </>
  );
}

const inp: React.CSSProperties = { width: "100%", padding: "8px 12px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "white", marginTop: 4 };
const btn: React.CSSProperties = { width: "auto", padding: "8px 20px", borderRadius: "var(--radius-full)", fontSize: 13 };
