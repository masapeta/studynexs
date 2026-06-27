"use client";

import { useEffect, useState } from "react";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { api, getApiErrorMessage } from "@/lib/api";
import { applyThemeColor, DEFAULT_ACCENT, getStoredThemeColor, normalizeThemeColor, themeColorForUi } from "@/lib/theme";
import { TOGGLEABLE_MODULES, isModuleOn } from "@/lib/modules";

export default function SettingsPage() {
  const [profile, setProfile] = useState<any>({ name: "", board: "", contact_email: "", contact_phone: "", address: {} });
  const [years, setYears] = useState<any[]>([]);
  const [modules, setModules] = useState<Record<string, boolean>>({});
  const [savingProfile, setSavingProfile] = useState(false);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [newYear, setNewYear] = useState({ year_label: "", start_date: "", end_date: "", is_active: false });
  const [addingYear, setAddingYear] = useState(false);

  useEffect(() => {
    api("/api/v1/school/profile")
      .then((r) => {
        const theme = themeColorForUi(r.data?.theme_color);
        setProfile({ ...(r.data || {}), address: r.data?.address || {}, theme_color: theme });
        setModules(r.data?.enabled_modules || {});
        if (normalizeThemeColor(r.data?.theme_color)) {
          applyThemeColor(r.data.theme_color, { persist: true });
        } else {
          applyThemeColor(theme, { persist: false });
        }
      })
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load school profile")));
    loadYears();
    return () => {
      const saved = getStoredThemeColor();
      applyThemeColor(saved ?? DEFAULT_ACCENT, { persist: false });
    };
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
          theme_color: profile.theme_color || DEFAULT_ACCENT,
        }),
      });
      setProfile({ ...(r.data || profile), address: r.data?.address || profile.address || {}, theme_color: themeColorForUi(r.data?.theme_color) });
      applyThemeColor(r.data?.theme_color ?? profile.theme_color, { persist: true });
      setMsg("School profile saved.");
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to save profile"));
    } finally {
      setSavingProfile(false);
    }
  }

  async function toggleModule(key: string, on: boolean) {
    const next = { ...modules, [key]: on };
    setModules(next);
    window.dispatchEvent(new CustomEvent("sn-modules", { detail: next }));
    try {
      await api("/api/v1/school/profile", {
        method: "PATCH",
        body: JSON.stringify({ enabled_modules: next }),
      });
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to update modules"));
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
      <PageHeaderCard title="School settings" subtitle="Profile, academic years, modules, and branding." />

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}
      {msg && <div className="card sn-inline-alert sn-inline-alert--success">{msg}</div>}

      {/* School profile */}
      <div className="card sn-settings-section">
        <h2>School Profile</h2>
        <div className="sn-settings-grid">
          <div><label className="stat-label">School name</label>
            <input className="form-input sn-inline-field" value={profile.name || ""} onChange={(e) => setProfile({ ...profile, name: e.target.value })} /></div>
          <div><label className="stat-label">Board</label>
            <input className="form-input sn-inline-field" value={profile.board || ""} onChange={(e) => setProfile({ ...profile, board: e.target.value })} /></div>
          <div><label className="stat-label">Contact email</label>
            <input className="form-input sn-inline-field" value={profile.contact_email || ""} onChange={(e) => setProfile({ ...profile, contact_email: e.target.value })} /></div>
          <div><label className="stat-label">Contact phone</label>
            <input className="form-input sn-inline-field" value={profile.contact_phone || ""} onChange={(e) => setProfile({ ...profile, contact_phone: e.target.value })} /></div>
          <div><label className="stat-label">City</label>
            <input className="form-input sn-inline-field" value={addr.city || ""} onChange={(e) => setProfile({ ...profile, address: { ...addr, city: e.target.value } })} /></div>
          <div><label className="stat-label">State</label>
            <input className="form-input sn-inline-field" value={addr.state || ""} onChange={(e) => setProfile({ ...profile, address: { ...addr, state: e.target.value } })} /></div>
        </div>

        {/* Brand colour — per-school theming */}
        <div style={{ marginTop: 20, paddingTop: 18, borderTop: "1px solid var(--border-light)" }}>
          <label className="stat-label">Brand colour</label>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8, flexWrap: "wrap" }}>
            <input
              type="color"
              value={profile.theme_color || DEFAULT_ACCENT}
              onChange={(e) => { setProfile({ ...profile, theme_color: e.target.value }); applyThemeColor(e.target.value, { persist: false }); }}
              style={{ width: 46, height: 38, border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", cursor: "pointer", background: "none", padding: 2 }}
            />
            <span style={{ fontSize: 13, color: "var(--text-secondary)", fontFamily: "monospace" }}>
              {(profile.theme_color || DEFAULT_ACCENT).toUpperCase()}
            </span>
            <div style={{ display: "flex", gap: 8, marginLeft: 8 }}>
              {["#ee6c4d", "#2563eb", "#16a34a", "#7c3aed", "#db2777", "#0891b2"].map((c) => (
                <button
                  key={c}
                  type="button"
                  title={c}
                  onClick={() => { setProfile({ ...profile, theme_color: c }); applyThemeColor(c, { persist: false }); }}
                  style={{ width: 26, height: 26, borderRadius: "50%", background: c, border: "2px solid #fff", boxShadow: "0 0 0 1px var(--border)", cursor: "pointer", padding: 0 }}
                />
              ))}
            </div>
          </div>
          <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 8 }}>
            Sets your school&apos;s accent across the whole app — preview is live; click Save Profile to keep it.
          </p>
        </div>

        <div style={{ marginTop: 16 }}>
          <button className="btn btn-primary" style={btn} onClick={saveProfile} disabled={savingProfile}>
            {savingProfile ? "Saving…" : "Save Profile"}
          </button>
        </div>
      </div>

      {/* Modules — per-school feature flags */}
      <div className="card sn-settings-section">
        <h2>Modules</h2>
        <p className="sn-settings-lead">
          Turn features on or off for your school — changes apply immediately.
        </p>
        <div className="sn-module-list">
          {TOGGLEABLE_MODULES.map((m) => {
            const on = isModuleOn(modules, m);
            return (
              <div key={m.key} className="sn-module-row">
                <div>
                  <div className="sn-module-label">{m.label}</div>
                  <div className="sn-module-desc">{m.desc}</div>
                </div>
                <button
                  type="button"
                  onClick={() => toggleModule(m.key, !on)}
                  aria-pressed={on}
                  title={on ? "Enabled" : "Disabled"}
                  style={{ width: 44, height: 26, borderRadius: 999, border: "none", cursor: "pointer", position: "relative", background: on ? "var(--accent)" : "var(--border)", transition: "0.2s", flexShrink: 0 }}
                >
                  <span style={{ position: "absolute", top: 3, left: on ? 21 : 3, width: 20, height: 20, borderRadius: "50%", background: "#fff", transition: "0.2s", boxShadow: "0 1px 2px rgba(0,0,0,0.25)" }} />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Academic years */}
      <div className="card sn-settings-section">
        <h2>Academic Years</h2>
        <table className="data-table sn-section-gap">
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
            <input className="form-input sn-inline-field" placeholder="2027-2028" value={newYear.year_label} onChange={(e) => setNewYear({ ...newYear, year_label: e.target.value })} /></div>
          <div><label className="stat-label">Start</label>
            <input type="date" className="form-input sn-inline-field" value={newYear.start_date} onChange={(e) => setNewYear({ ...newYear, start_date: e.target.value })} /></div>
          <div><label className="stat-label">End</label>
            <input type="date" className="form-input sn-inline-field" value={newYear.end_date} onChange={(e) => setNewYear({ ...newYear, end_date: e.target.value })} /></div>
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

const btn: React.CSSProperties = { width: "auto", padding: "8px 20px", borderRadius: "var(--radius-full)", fontSize: 13 };
