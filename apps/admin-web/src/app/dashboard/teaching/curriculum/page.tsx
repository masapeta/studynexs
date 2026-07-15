"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Check, ExternalLink, RefreshCw } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { TEACHING } from "@/lib/dashboard-routes";

type CurriculumPack = {
  id: string;
  status: string;
  board: string;
  book_title?: string | null;
  version: number;
  concept_count?: number;
};

type SpineOut = {
  concept_count: number;
  edge_count: number;
  chapters: {
    id: string;
    title: string;
    topics: { id: string; title: string; concepts: { id: string; slug: string; title: string }[] }[];
  }[];
};

type ConceptCard = {
  id: string;
  concept_id: string;
  title: string;
  status: string;
  concept_slug?: string;
  concept_title?: string;
};

type ReviewItem = {
  id: string;
  item_type: string;
  status: string;
  source: string;
  title: string;
  draft_payload: Record<string, unknown>;
  concept_slug?: string;
  concept_title?: string;
};

const btn: React.CSSProperties = {
  width: "auto",
  padding: "8px 18px",
  borderRadius: "var(--radius-full)",
  fontSize: 13,
};

export default function CurriculumManagementPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [packId, setPackId] = useState("");
  const [packs, setPacks] = useState<CurriculumPack[]>([]);
  const [spine, setSpine] = useState<SpineOut | null>(null);
  const [cards, setCards] = useState<ConceptCard[]>([]);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const selectedPack = packs.find((p) => p.id === packId);

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
        const items: CurriculumPack[] = r.data || [];
        setPacks(items);
        setPackId(items[0]?.id || "");
      })
      .catch(() => setPacks([]));
  }, [classId, subjectId]);

  const refreshPackData = useCallback(async () => {
    if (!packId) {
      setSpine(null);
      setCards([]);
      setReviewItems([]);
      setPendingCount(0);
      return;
    }
    try {
      const [graphRes, cardsRes, queueRes] = await Promise.all([
        api(`/api/v1/curriculum/packs/${packId}/graph`).catch(() => ({ data: null })),
        api(`/api/v1/curriculum/packs/${packId}/concept-cards`).catch(() => ({ data: [] })),
        api(`/api/v1/curriculum/content-review/queue?pack_id=${packId}&status=pending`).catch(() => ({
          data: { items: [], pending_count: 0 },
        })),
      ]);
      setSpine(graphRes.data || null);
      setCards(cardsRes.data || []);
      setReviewItems(queueRes.data?.items || []);
      setPendingCount(queueRes.data?.pending_count ?? 0);
    } catch {
      setSpine(null);
      setCards([]);
      setReviewItems([]);
    }
  }, [packId]);

  useEffect(() => {
    refreshPackData();
  }, [refreshPackData]);

  async function approvePack() {
    if (!packId) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/packs/${packId}/approve`, { method: "POST" });
      const r = await api(`/api/v1/curriculum/packs?class_id=${classId}&subject_id=${subjectId}`);
      setPacks(r.data || []);
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Pack approval failed"));
    } finally {
      setBusy(false);
    }
  }

  async function approveCard(cardId: string) {
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/concept-cards/${cardId}/approve`, { method: "POST" });
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Concept card approval failed"));
    } finally {
      setBusy(false);
    }
  }

  async function approveReview(itemId: string) {
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/content-review/items/${itemId}/approve`, { method: "POST" });
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Review approval failed"));
    } finally {
      setBusy(false);
    }
  }

  async function rejectReview(itemId: string) {
    const reason = window.prompt("Rejection reason (required):");
    if (!reason?.trim()) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/content-review/items/${itemId}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason: reason.trim() }),
      });
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Review rejection failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="sn-page">
      <PageHeaderCard
        title="Curriculum management"
        subtitle="Pack lifecycle, knowledge spine, concept cards, and the content review queue — one place for Curriculum Intelligence."
      >
        <Link href={TEACHING.documentIngest} className="sn-btn-ghost" style={btn}>
          <ExternalLink size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
          Document ingest
        </Link>
      </PageHeaderCard>

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
            <label className="stat-label">Curriculum pack</label>
            <AppSelect
              value={packId}
              onChange={setPackId}
              options={
                packs.length
                  ? packs.map((p) => ({
                      value: p.id,
                      label: `${p.status} · ${p.board}${p.book_title ? ` — ${p.book_title}` : ""} (v${p.version})`,
                    }))
                  : [{ value: "", label: "No packs — create via API or seed" }]
              }
            />
          </div>
        </div>

        {selectedPack && (
          <div style={{ marginTop: 16, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <span className="sn-badge">{selectedPack.status}</span>
            {selectedPack.status !== "approved" && (
              <button type="button" className="sn-btn-primary" style={btn} onClick={approvePack} disabled={busy}>
                <Check size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
                Approve pack
              </button>
            )}
            <button type="button" className="sn-btn-ghost" style={btn} onClick={() => refreshPackData()} disabled={busy || !packId}>
              <RefreshCw size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
              Refresh
            </button>
          </div>
        )}
      </section>

      {spine && (
        <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Knowledge spine</h3>
          <div className="sn-stat-row" style={{ marginBottom: 16 }}>
            <div>
              <span className="stat-label">Concepts</span>
              <strong>{spine.concept_count}</strong>
            </div>
            <div>
              <span className="stat-label">Graph edges</span>
              <strong>{spine.edge_count}</strong>
            </div>
            <div>
              <span className="stat-label">Pending reviews</span>
              <strong>{pendingCount}</strong>
            </div>
          </div>
          {spine.chapters.map((ch) => (
            <div key={ch.id} style={{ marginBottom: 12 }}>
              <strong style={{ fontSize: 14 }}>{ch.title}</strong>
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13 }}>
                {ch.topics.map((t) => (
                  <li key={t.id}>
                    {t.title}
                    {t.concepts.length > 0 && (
                      <span style={{ opacity: 0.75 }}> — {t.concepts.map((c) => c.title).join(", ")}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
        <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Concept cards</h3>
        {cards.length === 0 ? (
          <p style={{ margin: 0, opacity: 0.8, fontSize: 13 }}>No concept cards for this pack yet.</p>
        ) : (
          <table className="sn-table">
            <thead>
              <tr>
                <th>Concept</th>
                <th>Title</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {cards.map((c) => (
                <tr key={c.id}>
                  <td>{c.concept_title || c.concept_slug || c.concept_id}</td>
                  <td>{c.title}</td>
                  <td>{c.status}</td>
                  <td>
                    {c.status === "draft" && (
                      <button type="button" className="sn-btn-ghost" style={btn} onClick={() => approveCard(c.id)} disabled={busy}>
                        Approve
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="sn-glass-card" style={{ padding: 20 }}>
        <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Content review queue</h3>
        {reviewItems.length === 0 ? (
          <p style={{ margin: 0, opacity: 0.8, fontSize: 13 }}>No pending review items.</p>
        ) : (
          <table className="sn-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Title</th>
                <th>Source</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {reviewItems.map((item) => (
                <tr key={item.id}>
                  <td>{item.item_type.replace(/_/g, " ")}</td>
                  <td>
                    {item.title}
                    {item.concept_title && (
                      <div style={{ fontSize: 12, opacity: 0.75 }}>{item.concept_title}</div>
                    )}
                  </td>
                  <td>{item.source.replace(/_/g, " ")}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    {item.item_type === "concept_card_gap" && (
                      <button type="button" className="sn-btn-primary" style={btn} onClick={() => approveReview(item.id)} disabled={busy}>
                        Approve
                      </button>
                    )}
                    {item.item_type === "document_ingest" && (
                      <button type="button" className="sn-btn-primary" style={btn} onClick={() => approveReview(item.id)} disabled={busy}>
                        Mark reviewed
                      </button>
                    )}
                    <button type="button" className="sn-btn-ghost" style={{ ...btn, marginLeft: 8 }} onClick={() => rejectReview(item.id)} disabled={busy}>
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
