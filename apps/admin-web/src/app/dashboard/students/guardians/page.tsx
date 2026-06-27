"use client";

import { useEffect, useMemo, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageShell } from "@/components/layout/PageShell";
import { PersonMono } from "@/components/briefing/PersonMono";
import { Phone } from "lucide-react";

type ParentRow = {
  id: string;
  name: string;
  email?: string | null;
  mobile?: string | null;
  relationship: string;
  children: string[];
  child_label: string;
};

export default function GuardiansPage() {
  const [parents, setParents] = useState<ParentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    api<{ data: { parents: ParentRow[] } }>("/api/v1/ops/parents-directory")
      .then((r) => setParents(r.data?.parents || []))
      .catch((e) => setError(getApiErrorMessage(e, "Failed to load guardians")))
      .finally(() => setLoading(false));
  }, []);

  const directory = useMemo(() => parents, [parents]);

  return (
    <PageShell title="Guardians" subtitle="Linked parents and emergency contacts for enrolled students.">
      {error && <div className="gw-alert gw-alert-error">{error}</div>}

      {loading ? (
        <div className="gw-center">
          <div className="spinner" />
        </div>
      ) : directory.length === 0 ? (
        <p className="gw-muted">No linked guardians yet.</p>
      ) : (
        <div className="parents-directory-grid">
          {directory.map((p) => (
            <div key={p.id} className="parents-directory-card">
              <PersonMono name={p.name} size={36} />
              <div>
                <div className="gw-list-title">{p.name}</div>
                <div className="gw-list-meta">{p.child_label}</div>
                {p.mobile && (
                  <div className="gw-list-meta">
                    <Phone size={12} style={{ display: "inline", marginRight: 4 }} />
                    {p.mobile}
                  </div>
                )}
                {p.email && <div className="gw-list-meta">{p.email}</div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </PageShell>
  );
}
