"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Upload } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel, sortClasses } from "@/lib/format";

type CurriculumPack = { id: string; status: string; board: string; book_title?: string | null };
type IngestStatus = {
  indexed_topic_count: number;
  indexed_document_chunks: number;
  last_ingested_at?: string | null;
  recent_ingestions: {
    id: string;
    file_id: string;
    doc_type: string;
    status: string;
    version: number;
    chunks_indexed: number;
    source_name: string;
    created_at: string;
  }[];
};

const DOC_TYPES = [
  { value: "worksheet", label: "Worksheet" },
  { value: "notes", label: "Notes" },
  { value: "circular", label: "Circular" },
  { value: "other", label: "Other" },
];

const btn: React.CSSProperties = { width: "auto", padding: "8px 18px", borderRadius: "var(--radius-full)", fontSize: 13 };

async function uploadDocument(file: File): Promise<string> {
  if (file.size > 1024 * 1024) throw new Error("File too large (max 1 MB)");
  const fd = new FormData();
  fd.append("file", file);
  const res = await api<{ data: { id: string } }>("/api/v1/files/upload?category=document", {
    method: "POST",
    body: fd,
  });
  const id = res.data?.id;
  if (!id) throw new Error("Upload failed");
  return id;
}

export default function DocumentIngestPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [packId, setPackId] = useState("");
  const [packs, setPacks] = useState<CurriculumPack[]>([]);
  const [docType, setDocType] = useState("notes");
  const [status, setStatus] = useState<IngestStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<any>(r.items || r.data || []);
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!classId) return;
    api(`/api/v1/academic/subjects?class_id=${classId}`)
      .then((r) => {
        const items = r.items || r.data || (Array.isArray(r) ? r : []);
        setSubjects(items);
        setSubjectId(items[0]?.id || "");
      })
      .catch(() => {});
  }, [classId]);

  useEffect(() => {
    if (!classId || !subjectId) {
      setPacks([]);
      setPackId("");
      return;
    }
    api(`/api/v1/curriculum/packs?class_id=${classId}&subject_id=${subjectId}`)
      .then((r) => {
        const items: CurriculumPack[] = (r.data || []).filter(
          (p: CurriculumPack) => p.status === "approved"
        );
        setPacks(items);
        setPackId(items[0]?.id || "");
      })
      .catch(() => {});
  }, [classId, subjectId]);

  useEffect(() => {
    if (!packId) {
      setStatus(null);
      return;
    }
    api(`/api/v1/curriculum/packs/${packId}/ingest-status`)
      .then((r) => setStatus(r.data || null))
      .catch(() => setStatus(null));
  }, [packId]);

  async function refreshStatus() {
    if (!packId) return;
    const r = await api(`/api/v1/curriculum/packs/${packId}/ingest-status`);
    setStatus(r.data || null);
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !packId) return;
    setBusy(true);
    setError("");
    try {
      const fileId = await uploadDocument(file);
      await api(`/api/v1/curriculum/packs/${packId}/ingest-document`, {
        method: "POST",
        body: JSON.stringify({ file_id: fileId, doc_type: docType }),
      });
      await refreshStatus();
    } catch (err) {
      setError(getApiErrorMessage(err, "Document ingestion failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="sn-page">
      <PageHeaderCard
        title="Document Intelligence"
        subtitle="Upload worksheets, notes, or circulars to extend pack grounding for AI papers and lesson plans."
      />

      {error && <div className="card sn-inline-alert sn-inline-alert--error">{error}</div>}

      <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
        <div className="sn-form-grid" style={{ gap: 14 }}>
          <div>
            <label className="stat-label">Class</label>
            <AppSelect
              value={classId}
              onChange={setClassId}
              options={classes.map((c) => ({ value: c.id, label: formatClassLabel(c.grade, c.section) }))}
            />
          </div>
          <div>
            <label className="stat-label">Subject</label>
            <AppSelect
              value={subjectId}
              onChange={setSubjectId}
              options={subjects.map((s) => ({ value: s.id, label: s.name }))}
            />
          </div>
          <div>
            <label className="stat-label">Approved curriculum pack</label>
            <AppSelect
              value={packId}
              onChange={setPackId}
              options={
                packs.length
                  ? packs.map((p) => ({
                      value: p.id,
                      label: `${p.board}${p.book_title ? ` — ${p.book_title}` : ""}`,
                    }))
                  : [{ value: "", label: "No approved packs" }]
              }
            />
          </div>
          <div>
            <label className="stat-label">Document type</label>
            <AppSelect value={docType} onChange={setDocType} options={DOC_TYPES} />
          </div>
        </div>

        <div style={{ marginTop: 16, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <label style={{ ...btn, cursor: busy || !packId ? "not-allowed" : "pointer", opacity: busy || !packId ? 0.6 : 1 }}>
            <Upload size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
            Upload &amp; ingest PDF/image
            <input
              type="file"
              accept="application/pdf,image/jpeg,image/png,image/webp"
              onChange={handleUpload}
              disabled={busy || !packId}
              style={{ display: "none" }}
            />
          </label>
          <button type="button" className="sn-btn-ghost" style={btn} onClick={() => refreshStatus()} disabled={!packId || busy}>
            <RefreshCw size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
            Refresh status
          </button>
        </div>
      </section>

      {status && (
        <section className="sn-glass-card" style={{ padding: 20 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Ingestion status</h3>
          <div className="sn-stat-row" style={{ marginBottom: 16 }}>
            <div>
              <span className="stat-label">Structured topics</span>
              <strong>{status.indexed_topic_count}</strong>
            </div>
            <div>
              <span className="stat-label">Document chunks indexed</span>
              <strong>{status.indexed_document_chunks}</strong>
            </div>
            <div>
              <span className="stat-label">Last ingested</span>
              <strong>
                {status.last_ingested_at
                  ? new Date(status.last_ingested_at).toLocaleString()
                  : "—"}
              </strong>
            </div>
          </div>

          {status.recent_ingestions?.length > 0 && (
            <table className="sn-table">
              <thead>
                <tr>
                  <th>File</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Chunks</th>
                  <th>Version</th>
                </tr>
              </thead>
              <tbody>
                {status.recent_ingestions.map((row) => (
                  <tr key={row.id}>
                    <td>{row.source_name}</td>
                    <td>{row.doc_type}</td>
                    <td>{row.status}</td>
                    <td>{row.chunks_indexed}</td>
                    <td>v{row.version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
