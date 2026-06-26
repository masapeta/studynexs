"use client";

import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import { Bus } from "lucide-react";

type Route = {
  id: string;
  route_name: string;
  vehicle_number?: string;
  driver_name?: string;
  capacity?: number;
  student_count?: number;
  student_names?: string[];
};

export default function TransportPage() {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/ops/transport/routes")
      .then((r) => setRoutes(r.data || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load routes")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PageShell title="Transport" subtitle={`${routes.length} active routes`}>
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      {loading ? (
        <div className="gw-center"><div className="spinner" /></div>
      ) : routes.length === 0 ? (
        <p className="gw-muted">No routes configured yet.</p>
      ) : (
        <div className="gw-transport-grid">
          {routes.map((rt) => {
            const cap = rt.capacity || 30;
            const used = rt.student_count || 0;
            const pct = cap > 0 ? Math.round((used / cap) * 100) : 0;
            const names = rt.student_names || [];
            return (
              <div key={rt.id} className="gw-card gw-route-card">
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <Bus size={16} className="briefing-tone-brass" />
                  <span className="gw-route-title">{rt.route_name}</span>
                </div>
                <div className="gw-route-meta">
                  Driver · {rt.driver_name || "—"} | {rt.vehicle_number || "—"}
                </div>
                <div style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  {used} of {cap} seats
                  <span style={{ float: "right" }}>{pct}%</span>
                </div>
                <div className="gw-capacity-bar">
                  <div className="gw-capacity-fill" style={{ width: `${pct}%` }} />
                </div>
                <div className="gw-chip-row">
                  {names.length ? names.map((n, i) => (
                    <span key={`${rt.id}-${i}-${n}`} className="gw-chip">{n.split(" ")[0]}</span>
                  )) : (
                    <span className="gw-muted" style={{ fontSize: 12 }}>No students assigned</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </PageShell>
  );
}
