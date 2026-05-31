"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function StaffPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchStaff();
  }, []);

  async function fetchStaff() {
    setLoading(true);
    try {
      const res = await api(`/api/v1/users?role=teacher&search=${search}&page_size=20`);
      setUsers(res.items || res.data || []);
      setTotal(res.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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
          <button className="btn btn-primary" style={{ width: "auto", padding: "10px 20px" }}>
            + Add Staff
          </button>
        </div>
      </div>

      <div className="data-table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
              <th>Email</th>
              <th>Mobile</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ textAlign: "center", padding: 40 }}>
                <div className="spinner" style={{ margin: "0 auto" }} />
              </td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
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
                  <td><button className="card-menu">⋯</button></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
