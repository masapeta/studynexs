"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { BedDouble, Plus } from "lucide-react";

const inp: React.CSSProperties = { marginTop: 4 };

function genderBadge(g: string) {
  return g === "boys" ? "badge-info" : g === "girls" ? "badge-danger" : "badge-success";
}

export default function ResidentialPage() {
  const [blocks, setBlocks] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [residents, setResidents] = useState<any[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ block_name: "", block_gender: "mixed", warden_name: "", warden_contact: "", total_rooms: 0 });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => { load(); }, []);

  function load() {
    api("/api/v1/ops/residential/blocks")
      .then((r) => setBlocks(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load blocks")));
  }

  async function openBlock(b: any) {
    setSelected(b);
    try {
      const r = await api(`/api/v1/ops/residential/blocks/${b.id}/residents`);
      setResidents(r.data || []);
    } catch {
      setResidents([]);
    }
  }

  async function addBlock() {
    if (!form.block_name) { setError("Block name is required."); return; }
    setSaving(true);
    setError("");
    try {
      await api("/api/v1/ops/residential/blocks", {
        method: "POST",
        body: JSON.stringify({ ...form, total_rooms: Number(form.total_rooms) }),
      });
      setForm({ block_name: "", block_gender: "mixed", warden_name: "", warden_contact: "", total_rooms: 0 });
      setShowAdd(false);
      load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to add block"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="card bento-glass" style={{ marginBottom: 24, padding: "16px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>Residential</h1>
          <p style={{ margin: "4px 0 0", color: "var(--text-muted)", fontSize: 13 }}>Hostel blocks and room allocations.</p>
        </div>
        <button className="btn btn-primary" style={{ width: "auto", padding: "8px 18px" }} onClick={() => setShowAdd((v) => !v)}>
          <Plus size={16} /> Add Block
        </button>
      </div>

      {error && <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>{error}</div>}

      {showAdd && (
        <div className="card" style={{ marginBottom: 24, padding: 24 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, marginTop: 0, marginBottom: 16 }}>New Block</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div><label className="stat-label">Block name</label><input className="form-input" style={inp} value={form.block_name} onChange={(e) => setForm({ ...form, block_name: e.target.value })} placeholder="Nehru Block (Boys)" /></div>
            <div><label className="stat-label">Type</label>
              <AppSelect
                variant="field"
                value={form.block_gender}
                onChange={(v) => setForm({ ...form, block_gender: v })}
                aria-label="Block type"
                options={[
                  { value: "boys", label: "Boys" },
                  { value: "girls", label: "Girls" },
                  { value: "mixed", label: "Mixed" },
                ]}
              />
            </div>
            <div><label className="stat-label">Warden name</label><input className="form-input" style={inp} value={form.warden_name} onChange={(e) => setForm({ ...form, warden_name: e.target.value })} /></div>
            <div><label className="stat-label">Warden contact</label><input className="form-input" style={inp} value={form.warden_contact} onChange={(e) => setForm({ ...form, warden_contact: e.target.value })} /></div>
            <div><label className="stat-label">Total rooms</label><input type="number" className="form-input" style={inp} value={form.total_rooms} onChange={(e) => setForm({ ...form, total_rooms: Number(e.target.value) })} /></div>
          </div>
          <button className="btn btn-primary" style={{ width: "auto", padding: "8px 20px", marginTop: 16 }} onClick={addBlock} disabled={saving}>
            {saving ? "Saving…" : "Create Block"}
          </button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 16, marginBottom: 24 }}>
        {blocks.map((b) => (
          <div key={b.id} className="card" style={{ padding: 20, cursor: "pointer", borderColor: selected?.id === b.id ? "var(--accent)" : undefined }} onClick={() => openBlock(b)}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <div className="stat-icon-container icon-purple"><BedDouble size={20} /></div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700 }}>{b.block_name}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{b.total_rooms} rooms</div>
              </div>
              <span className={`badge ${genderBadge(b.block_gender)}`} style={{ textTransform: "capitalize" }}>{b.block_gender}</span>
            </div>
            <div style={{ fontSize: 13, color: "var(--text-secondary)", display: "flex", justifyContent: "space-between" }}>
              <span>Warden: {b.warden_name || "—"}</span>
              <span className="badge badge-info">{b.resident_count} residents</span>
            </div>
          </div>
        ))}
        {blocks.length === 0 && <div style={{ color: "var(--text-muted)", fontSize: 14 }}>No blocks yet. Add one above.</div>}
      </div>

      {selected && (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "14px 22px", fontWeight: 700, borderBottom: "1px solid var(--border-light)" }}>
            {selected.block_name} — {residents.length} residents
          </div>
          {residents.length === 0 ? (
            <div style={{ padding: 24, color: "var(--text-muted)", fontSize: 14 }}>No residents allocated to this block.</div>
          ) : (
            <table className="data-table">
              <thead><tr><th>Room</th><th>Admission No</th><th>Student</th></tr></thead>
              <tbody>
                {residents.map((s: any) => (
                  <tr key={s.student_id}>
                    <td style={{ fontWeight: 600 }}>{s.room_number || "—"}</td>
                    <td>{s.admission_no}</td>
                    <td>{s.name}</td>
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
