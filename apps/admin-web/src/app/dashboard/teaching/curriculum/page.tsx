"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Check, Clock, ExternalLink, Plus, RefreshCw, Save } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { AppSelect } from "@/components/ui/AppSelect";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { CurriculumGroundingBadge } from "@/components/curriculum/CurriculumGroundingBadge";
import { formatClassLabel, sortClasses } from "@/lib/format";
import { TEACHING } from "@/lib/dashboard-routes";

type CurriculumPack = {
  id: string;
  status: string;
  board: string;
  book_title?: string | null;
  version: number;
  concept_count?: number;
  approved_at?: string | null;
};

type LearningOutcome = {
  id: string;
  code?: string | null;
  description: string;
};

type PackTopic = {
  id: string;
  title: string;
  order_index: number;
  concepts?: string[] | null;
  learning_outcomes?: LearningOutcome[];
};

type PackChapter = {
  id: string;
  number?: string | null;
  title: string;
  order_index: number;
  topics: PackTopic[];
  learning_outcomes?: LearningOutcome[];
};

type PackDetail = CurriculumPack & {
  chapters: PackChapter[];
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

type AcademicYear = { id: string; name: string; is_active?: boolean };

type AuditEvent = {
  id: string;
  event_type: string;
  actor_name?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

type GroundingPreview = {
  pack_id: string;
  pack_status: string;
  pack_version: number;
  source_count: number;
  context_preview: string;
  sources: Array<Record<string, unknown>>;
};

const EVENT_LABELS: Record<string, string> = {
  pack_created: "Pack created",
  pack_updated: "Pack updated",
  chapter_added: "Chapter added",
  topic_added: "Topic added",
  learning_outcome_added: "Learning outcome added",
  learning_outcome_updated: "Learning outcome updated",
  pack_approved: "Pack approved",
  rag_index_succeeded: "Indexed for AI retrieval",
  rag_index_failed: "Indexing failed",
  kg_spine_started: "Knowledge graph spine started",
  kg_spine_succeeded: "Knowledge graph spine built",
  kg_spine_failed: "Knowledge graph spine failed",
};

function formatEventDetail(event: AuditEvent): string {
  const m = event.metadata || {};
  switch (event.event_type) {
    case "chapter_added":
    case "topic_added":
      return String(m.title || "");
    case "pack_approved":
      return `Version ${m.version ?? "?"}`;
    case "rag_index_succeeded":
      return `${m.vector_count ?? 0} vectors indexed`;
    case "rag_index_failed":
      return String(m.error || "Unknown error");
    case "learning_outcome_added":
      return String(m.code || m.outcome_id || "");
    default:
      return "";
  }
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "6px 10px",
  fontSize: 13,
  borderRadius: 6,
  border: "1px solid var(--border-subtle)",
};

const btn: React.CSSProperties = {
  width: "auto",
  padding: "8px 18px",
  borderRadius: "var(--radius-full)",
  fontSize: 13,
};

const emptyChapterForm = () => ({
  number: "",
  title: "",
  topicTitle: "",
  topicConcepts: "",
});

const emptyCreateForm = (academicYearId: string) => ({
  board: "SSC",
  book_title: "",
  publisher: "",
  edition: "",
  academic_year_id: academicYearId,
});

export default function CurriculumManagementPage() {
  const [classes, setClasses] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [packId, setPackId] = useState("");
  const [packs, setPacks] = useState<CurriculumPack[]>([]);
  const [packDetail, setPackDetail] = useState<PackDetail | null>(null);
  const [spine, setSpine] = useState<SpineOut | null>(null);
  const [cards, setCards] = useState<ConceptCard[]>([]);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showCreatePack, setShowCreatePack] = useState(false);
  const [createForm, setCreateForm] = useState(emptyCreateForm(""));
  const [chapterForm, setChapterForm] = useState(emptyChapterForm());
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [groundingPreview, setGroundingPreview] = useState<GroundingPreview | null>(null);
  const [editBookTitle, setEditBookTitle] = useState("");
  const [editBoard, setEditBoard] = useState("SSC");
  const [addTopicChapterId, setAddTopicChapterId] = useState("");
  const [newTopicTitle, setNewTopicTitle] = useState("");
  const [loScope, setLoScope] = useState<"topic" | "chapter">("topic");
  const [loTargetId, setLoTargetId] = useState("");
  const [newLoCode, setNewLoCode] = useState("");
  const [newLoDescription, setNewLoDescription] = useState("");

  const selectedPack = packs.find((p) => p.id === packId);
  const isDraft = selectedPack?.status === "draft";

  async function loadPacks(nextClassId = classId, nextSubjectId = subjectId, preferPackId?: string) {
    if (!nextClassId || !nextSubjectId) {
      setPacks([]);
      setPackId("");
      return;
    }
    const r = await api(`/api/v1/curriculum/packs?class_id=${nextClassId}&subject_id=${nextSubjectId}`);
    const items: CurriculumPack[] = r.data || [];
    setPacks(items);
    if (preferPackId && items.some((p) => p.id === preferPackId)) {
      setPackId(preferPackId);
    } else {
      setPackId(items[0]?.id || "");
    }
  }

  useEffect(() => {
    api("/api/v1/academic/classes?page_size=100")
      .then((r) => {
        const items = sortClasses<any>(r.items || r.data || []);
        setClasses(items);
        if (items[0]) setClassId(items[0].id);
      })
      .catch(() => {});
    api("/api/v1/school/academic-years")
      .then((r) => {
        const items: AcademicYear[] = r.data || r.items || [];
        setAcademicYears(items);
        const active = items.find((y) => y.is_active) || items[0];
        if (active) setCreateForm(emptyCreateForm(active.id));
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
    loadPacks().catch(() => setPacks([]));
  }, [classId, subjectId]);

  const refreshPackData = useCallback(async () => {
    if (!packId) {
      setPackDetail(null);
      setSpine(null);
      setCards([]);
      setReviewItems([]);
      setPendingCount(0);
      setAudit([]);
      setGroundingPreview(null);
      return;
    }
    try {
      const packStatus = packs.find((p) => p.id === packId)?.status;
      const [detailRes, graphRes, cardsRes, queueRes, auditRes, groundingRes] = await Promise.all([
        api(`/api/v1/curriculum/packs/${packId}`).catch(() => ({ data: null })),
        api(`/api/v1/curriculum/packs/${packId}/graph`).catch(() => ({ data: null })),
        api(`/api/v1/curriculum/packs/${packId}/concept-cards`).catch(() => ({ data: [] })),
        api(`/api/v1/curriculum/content-review/queue?pack_id=${packId}&status=pending`).catch(() => ({
          data: { items: [], pending_count: 0 },
        })),
        api(`/api/v1/curriculum/packs/${packId}/audit`).catch(() => ({ data: [] })),
        packStatus === "approved"
          ? api(`/api/v1/curriculum/packs/${packId}/grounding`).catch(() => ({ data: null }))
          : Promise.resolve({ data: null }),
      ]);
      const detail = detailRes.data || null;
      setPackDetail(detail);
      setEditBookTitle(detail?.book_title || "");
      setEditBoard(detail?.board || "SSC");
      const firstCh = detail?.chapters?.[0];
      if (firstCh) {
        setAddTopicChapterId(firstCh.id);
        setLoTargetId(firstCh.topics?.[0]?.id || firstCh.id);
      }
      setSpine(graphRes.data || null);
      setCards(cardsRes.data || []);
      setReviewItems(queueRes.data?.items || []);
      setPendingCount(queueRes.data?.pending_count ?? 0);
      setAudit(auditRes.data || []);
      setGroundingPreview(groundingRes.data || null);
    } catch {
      setPackDetail(null);
      setSpine(null);
      setCards([]);
      setReviewItems([]);
    }
  }, [packId, packs]);

  useEffect(() => {
    refreshPackData();
  }, [refreshPackData]);

  async function createPack() {
    if (!classId || !subjectId || !createForm.academic_year_id || !createForm.board.trim()) {
      setError("Class, subject, academic year, and board are required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const res = await api<{ data: CurriculumPack }>("/api/v1/curriculum/packs", {
        method: "POST",
        body: JSON.stringify({
          class_id: classId,
          subject_id: subjectId,
          academic_year_id: createForm.academic_year_id,
          board: createForm.board.trim(),
          book_title: createForm.book_title.trim() || undefined,
          publisher: createForm.publisher.trim() || undefined,
          edition: createForm.edition.trim() || undefined,
        }),
      });
      await loadPacks(classId, subjectId, res.data.id);
      setShowCreatePack(false);
      setChapterForm(emptyChapterForm());
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not create curriculum pack."));
    } finally {
      setBusy(false);
    }
  }

  async function addChapter() {
    if (!packId || !chapterForm.title.trim()) {
      setError("Chapter title is required.");
      return;
    }
    const concepts = chapterForm.topicConcepts
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    const topics = chapterForm.topicTitle.trim()
      ? [{ title: chapterForm.topicTitle.trim(), concepts: concepts.length ? concepts : undefined }]
      : [];

    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/packs/${packId}/chapters`, {
        method: "POST",
        body: JSON.stringify({
          number: chapterForm.number.trim() || undefined,
          title: chapterForm.title.trim(),
          topics,
        }),
      });
      setChapterForm(emptyChapterForm());
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not add chapter."));
    } finally {
      setBusy(false);
    }
  }

  async function approvePack() {
    if (!packId) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/packs/${packId}/approve`, { method: "POST" });
      await loadPacks();
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

  async function savePackMeta() {
    if (!packId || !packDetail) return;
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/packs/${packId}`, {
        method: "PUT",
        body: JSON.stringify({
          board: editBoard.trim() || packDetail.board,
          book_title: editBookTitle.trim() || packDetail.book_title,
        }),
      });
      await loadPacks();
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not save pack metadata."));
    } finally {
      setBusy(false);
    }
  }

  async function addTopic() {
    if (!addTopicChapterId || !newTopicTitle.trim()) {
      setError("Select a chapter and enter a topic title.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await api(`/api/v1/curriculum/chapters/${addTopicChapterId}/topics`, {
        method: "POST",
        body: JSON.stringify({ title: newTopicTitle.trim() }),
      });
      setNewTopicTitle("");
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not add topic."));
    } finally {
      setBusy(false);
    }
  }

  async function addLearningOutcome() {
    if (!loTargetId || !newLoDescription.trim()) {
      setError("Select a target and enter a learning outcome description.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const path =
        loScope === "topic"
          ? `/api/v1/curriculum/topics/${loTargetId}/learning-outcomes`
          : `/api/v1/curriculum/chapters/${loTargetId}/learning-outcomes`;
      await api(path, {
        method: "POST",
        body: JSON.stringify({
          code: newLoCode.trim() || null,
          description: newLoDescription.trim(),
        }),
      });
      setNewLoCode("");
      setNewLoDescription("");
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not add learning outcome."));
    } finally {
      setBusy(false);
    }
  }

  async function updateLoDescription(outcomeId: string, description: string) {
    if (!description.trim() || !packId) return;
    setBusy(true);
    try {
      await api(`/api/v1/curriculum/learning-outcomes/${outcomeId}`, {
        method: "PUT",
        body: JSON.stringify({ description: description.trim() }),
      });
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not update learning outcome."));
    } finally {
      setBusy(false);
    }
  }

  async function updateTopicTitle(topicId: string, title: string) {
    if (!title.trim() || !packId) return;
    setBusy(true);
    try {
      await api(`/api/v1/curriculum/topics/${topicId}`, {
        method: "PUT",
        body: JSON.stringify({ title: title.trim() }),
      });
      await refreshPackData();
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not update topic."));
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

  const structureChapters = packDetail?.chapters?.length
    ? packDetail.chapters
    : spine?.chapters?.map((ch) => ({
        id: ch.id,
        number: null,
        title: ch.title,
        order_index: 0,
        topics: ch.topics.map((t) => ({
          id: t.id,
          title: t.title,
          order_index: 0,
          concepts: t.concepts.map((c) => c.title),
        })),
      })) || [];

  const chapterOptions = (packDetail?.chapters || []).map((ch) => ({
    value: ch.id,
    label: ch.title,
  }));
  const topicOptions = (packDetail?.chapters || []).flatMap((ch) =>
    (ch.topics || []).map((t) => ({ value: t.id, label: `${ch.title} › ${t.title}` }))
  );

  return (
    <div className="sn-page">
      <PageHeaderCard
        title="Curriculum management"
        subtitle="Build draft curriculum packs, approve for institutional memory, and manage the knowledge spine."
      >
        <Link href={TEACHING.documentIngest} className="sn-btn-ghost" style={btn}>
          <ExternalLink size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
          Document ingest
        </Link>
      </PageHeaderCard>

      {error && (
        <div className="card sn-inline-alert sn-inline-alert--error" role="alert">
          {error}
        </div>
      )}

      <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
        <div className="sn-form-grid" style={{ gap: 14 }}>
          <div>
            <label className="stat-label" htmlFor="curriculum-class">
              Class
            </label>
            <AppSelect
              value={classId}
              onChange={setClassId}
              options={classes.map((c) => ({ value: c.id, label: formatClassLabel(c.grade, c.section) }))}
            />
          </div>
          <div>
            <label className="stat-label" htmlFor="curriculum-subject">
              Subject
            </label>
            <AppSelect
              value={subjectId}
              onChange={setSubjectId}
              options={subjects.map((s) => ({ value: s.id, label: s.name }))}
            />
          </div>
          <div>
            <label className="stat-label" htmlFor="curriculum-pack">
              Curriculum pack
            </label>
            <AppSelect
              value={packId}
              onChange={setPackId}
              options={
                packs.length
                  ? packs.map((p) => ({
                      value: p.id,
                      label: `${p.status} · ${p.board}${p.book_title ? ` — ${p.book_title}` : ""} (v${p.version})`,
                    }))
                  : [{ value: "", label: "No packs yet — create a draft below" }]
              }
            />
          </div>
        </div>

        <div style={{ marginTop: 16, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <button
            type="button"
            className="sn-btn-primary"
            style={btn}
            onClick={() => setShowCreatePack((v) => !v)}
            disabled={busy || !classId || !subjectId}
          >
            <Plus size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
            {showCreatePack ? "Hide create form" : "New draft pack"}
          </button>
          {isDraft && packId && (
            <button type="button" className="sn-btn-ghost" style={btn} onClick={savePackMeta} disabled={busy}>
              <Save size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
              Save draft
            </button>
          )}
          {selectedPack && (
            <>
              <span className="sn-badge">{selectedPack.status}</span>
              {selectedPack.approved_at && (
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Approved {new Date(selectedPack.approved_at).toLocaleString()}
                </span>
              )}
              {isDraft && (
                <button type="button" className="sn-btn-primary" style={btn} onClick={approvePack} disabled={busy}>
                  <Check size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
                  Approve pack
                </button>
              )}
            </>
          )}
          <button
            type="button"
            className="sn-btn-ghost"
            style={btn}
            onClick={() => refreshPackData()}
            disabled={busy || !packId}
          >
            <RefreshCw size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
            Refresh
          </button>
        </div>
      </section>

      {packId && (
        <div className="sn-two-col" style={{ gap: 16, alignItems: "start", marginBottom: 16 }}>
          <section className="sn-glass-card" style={{ padding: 20 }}>
            <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Audit trail</h3>
            {audit.length === 0 ? (
              <p style={{ margin: 0, color: "var(--text-muted)", fontSize: 13 }}>No audit events yet.</p>
            ) : (
              <ul className="sn-list-plain">
                {audit.map((e) => (
                  <li key={e.id} style={{ padding: "8px 0", borderBottom: "1px solid var(--border-subtle)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                      <Clock size={12} aria-hidden />
                      <strong>{EVENT_LABELS[e.event_type] || e.event_type}</strong>
                    </div>
                    <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                      {new Date(e.created_at).toLocaleString()}
                      {e.actor_name ? ` · ${e.actor_name}` : ""}
                      {formatEventDetail(e) ? ` · ${formatEventDetail(e)}` : ""}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {!isDraft && groundingPreview && (
            <section className="sn-glass-card" style={{ padding: 20 }}>
              <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Grounding preview</h3>
              <CurriculumGroundingBadge
                packId={groundingPreview.pack_id}
                packStatus={groundingPreview.pack_status}
                packVersion={groundingPreview.pack_version}
                grounded
                compact
              />
              <p style={{ margin: "12px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
                {groundingPreview.source_count} source(s) · preview:
              </p>
              <pre
                style={{
                  marginTop: 8,
                  padding: 12,
                  fontSize: 11,
                  lineHeight: 1.5,
                  background: "var(--bg-subtle)",
                  borderRadius: 8,
                  whiteSpace: "pre-wrap",
                  maxHeight: 200,
                  overflow: "auto",
                }}
              >
                {groundingPreview.context_preview}
              </pre>
            </section>
          )}
        </div>
      )}

      {isDraft && packId && packDetail && (
        <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Pack metadata</h3>
          <div className="sn-form-grid" style={{ gap: 14 }}>
            <div>
              <label className="stat-label" htmlFor="edit-board">
                Board
              </label>
              <input
                id="edit-board"
                className="form-input"
                value={editBoard}
                onChange={(e) => setEditBoard(e.target.value)}
                aria-label="Board"
              />
            </div>
            <div>
              <label className="stat-label" htmlFor="edit-book">
                Book title
              </label>
              <input
                id="edit-book"
                className="form-input"
                value={editBookTitle}
                onChange={(e) => setEditBookTitle(e.target.value)}
                aria-label="Book title"
              />
            </div>
          </div>
        </section>
      )}

      {showCreatePack && (
        <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Create draft pack</h3>
          <p style={{ margin: "0 0 16px", fontSize: 13, color: "var(--text-muted)" }}>
            Define board and book metadata, then add chapters before approval.
          </p>
          <div className="sn-form-grid" style={{ gap: 14 }}>
            <div>
              <label className="stat-label" htmlFor="pack-year">
                Academic year
              </label>
              <AppSelect
                value={createForm.academic_year_id}
                onChange={(v) => setCreateForm((f) => ({ ...f, academic_year_id: v }))}
                options={academicYears.map((y) => ({
                  value: y.id,
                  label: y.is_active ? `${y.name} (active)` : y.name,
                }))}
              />
            </div>
            <div>
              <label className="stat-label" htmlFor="pack-board">
                Board
              </label>
              <input
                id="pack-board"
                className="form-input"
                value={createForm.board}
                onChange={(e) => setCreateForm((f) => ({ ...f, board: e.target.value }))}
                placeholder="e.g. SSC, CBSE"
              />
            </div>
            <div>
              <label className="stat-label" htmlFor="pack-book">
                Book title
              </label>
              <input
                id="pack-book"
                className="form-input"
                value={createForm.book_title}
                onChange={(e) => setCreateForm((f) => ({ ...f, book_title: e.target.value }))}
                placeholder="e.g. NCERT Mathematics"
              />
            </div>
            <div>
              <label className="stat-label" htmlFor="pack-publisher">
                Publisher
              </label>
              <input
                id="pack-publisher"
                className="form-input"
                value={createForm.publisher}
                onChange={(e) => setCreateForm((f) => ({ ...f, publisher: e.target.value }))}
              />
            </div>
            <div>
              <label className="stat-label" htmlFor="pack-edition">
                Edition
              </label>
              <input
                id="pack-edition"
                className="form-input"
                value={createForm.edition}
                onChange={(e) => setCreateForm((f) => ({ ...f, edition: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <button type="button" className="sn-btn-primary" style={btn} onClick={createPack} disabled={busy}>
              Save draft pack
            </button>
          </div>
        </section>
      )}

      {isDraft && packId && (
        <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>Add content</h3>
          <div className="sn-form-grid" style={{ gap: 14 }}>
            <div>
              <label className="stat-label" htmlFor="chapter-number">
                Chapter number
              </label>
              <input
                id="chapter-number"
                className="form-input"
                value={chapterForm.number}
                onChange={(e) => setChapterForm((f) => ({ ...f, number: e.target.value }))}
                placeholder="1"
              />
            </div>
            <div>
              <label className="stat-label" htmlFor="chapter-title">
                Chapter title
              </label>
              <input
                id="chapter-title"
                className="form-input"
                value={chapterForm.title}
                onChange={(e) => setChapterForm((f) => ({ ...f, title: e.target.value }))}
                placeholder="e.g. Algebra"
              />
            </div>
            <div style={{ display: "flex", alignItems: "flex-end" }}>
              <button type="button" className="sn-btn-primary" style={btn} onClick={addChapter} disabled={busy}>
                Add chapter
              </button>
            </div>
          </div>
          <div className="sn-form-grid" style={{ gap: 14, marginTop: 16 }}>
            <div>
              <label className="stat-label">Chapter for topic</label>
              <AppSelect
                value={addTopicChapterId}
                onChange={setAddTopicChapterId}
                aria-label="Chapter for topic"
                options={chapterOptions.length ? chapterOptions : [{ value: "", label: "Add a chapter first" }]}
              />
            </div>
            <div>
              <label className="stat-label">Topic title</label>
              <input
                className="form-input"
                value={newTopicTitle}
                onChange={(e) => setNewTopicTitle(e.target.value)}
                placeholder="e.g. Linear Equations"
              />
            </div>
            <div style={{ display: "flex", alignItems: "flex-end" }}>
              <button type="button" className="sn-btn-secondary" style={btn} onClick={addTopic} disabled={busy || !chapterOptions.length}>
                Add topic
              </button>
            </div>
          </div>
          <div className="sn-form-grid" style={{ gap: 14, marginTop: 16 }}>
            <div>
              <label className="stat-label">LO scope</label>
              <AppSelect
                value={loScope}
                onChange={(v) => {
                  setLoScope(v as "topic" | "chapter");
                  setLoTargetId("");
                }}
                aria-label="Learning outcome scope"
                options={[
                  { value: "topic", label: "Topic" },
                  { value: "chapter", label: "Chapter" },
                ]}
              />
            </div>
            <div>
              <label className="stat-label">Target</label>
              <AppSelect
                value={loTargetId}
                onChange={setLoTargetId}
                aria-label="Learning outcome target"
                options={
                  loScope === "topic"
                    ? topicOptions.length
                      ? topicOptions
                      : [{ value: "", label: "Add a topic first" }]
                    : chapterOptions.length
                      ? chapterOptions
                      : [{ value: "", label: "Add a chapter first" }]
                }
              />
            </div>
            <div>
              <label className="stat-label">LO code (optional)</label>
              <input style={inputStyle} value={newLoCode} onChange={(e) => setNewLoCode(e.target.value)} placeholder="LO-1" />
            </div>
            <div>
              <label className="stat-label">LO description</label>
              <input style={inputStyle} value={newLoDescription} onChange={(e) => setNewLoDescription(e.target.value)} placeholder="Student can…" />
            </div>
            <div style={{ display: "flex", alignItems: "flex-end" }}>
              <button type="button" className="sn-btn-secondary" style={btn} onClick={addLearningOutcome} disabled={busy}>
                Add learning outcome
              </button>
            </div>
          </div>
          <details style={{ marginTop: 16 }}>
            <summary style={{ fontSize: 13, cursor: "pointer", color: "var(--text-muted)" }}>
              Optional: add chapter with first topic and concepts in one step
            </summary>
            <div className="sn-form-grid" style={{ gap: 14, marginTop: 12 }}>
              <div>
                <label className="stat-label" htmlFor="topic-title">
                  First topic title
                </label>
                <input
                  id="topic-title"
                  className="form-input"
                  value={chapterForm.topicTitle}
                  onChange={(e) => setChapterForm((f) => ({ ...f, topicTitle: e.target.value }))}
                  placeholder="Linear equations"
                />
              </div>
              <div>
                <label className="stat-label" htmlFor="topic-concepts">
                  Topic concepts (comma-separated)
                </label>
                <input
                  id="topic-concepts"
                  className="form-input"
                  value={chapterForm.topicConcepts}
                  onChange={(e) => setChapterForm((f) => ({ ...f, topicConcepts: e.target.value }))}
                  placeholder="slope, intercept"
                />
              </div>
            </div>
          </details>
        </section>
      )}

      {structureChapters.length > 0 && (
        <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: 15 }}>
            {isDraft ? "Draft curriculum structure" : "Knowledge spine"}
          </h3>
          {spine && (
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
          )}
          {structureChapters.map((ch) => (
            <div key={ch.id} style={{ marginBottom: 12 }}>
              <strong style={{ fontSize: 14 }}>
                {ch.number ? `${ch.number}. ` : ""}
                {ch.title}
              </strong>
              {(ch as PackChapter).learning_outcomes?.map((lo) => (
                <div key={lo.id} style={{ marginLeft: 12, marginTop: 6, fontSize: 12 }}>
                  {isDraft ? (
                    <input
                      style={inputStyle}
                      defaultValue={lo.description}
                      aria-label="Learning outcome"
                      onBlur={(e) => {
                        if (e.target.value.trim() !== lo.description) {
                          updateLoDescription(lo.id, e.target.value);
                        }
                      }}
                    />
                  ) : (
                    <span>LO: {lo.code ? `${lo.code} — ` : ""}{lo.description}</span>
                  )}
                </div>
              ))}
              <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13 }}>
                {ch.topics.map((t) => (
                  <li key={t.id}>
                    {isDraft ? (
                      <input
                        style={{ ...inputStyle, marginBottom: 4 }}
                        defaultValue={t.title}
                        aria-label={`Topic ${t.title}`}
                        onBlur={(e) => {
                          if (e.target.value.trim() !== t.title) {
                            updateTopicTitle(t.id, e.target.value);
                          }
                        }}
                      />
                    ) : (
                      t.title
                    )}
                    {t.concepts && t.concepts.length > 0 && (
                      <span style={{ opacity: 0.75 }}> — {t.concepts.join(", ")}</span>
                    )}
                    {(t as PackTopic).learning_outcomes?.map((lo) => (
                      <div key={lo.id} style={{ marginTop: 4, fontSize: 12 }}>
                        {isDraft ? (
                          <input
                            style={inputStyle}
                            defaultValue={lo.description}
                            aria-label="Topic learning outcome"
                            onBlur={(e) => {
                              if (e.target.value.trim() !== lo.description) {
                                updateLoDescription(lo.id, e.target.value);
                              }
                            }}
                          />
                        ) : (
                          <span>LO: {lo.code ? `${lo.code} — ` : ""}{lo.description}</span>
                        )}
                      </div>
                    ))}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      )}

      {isDraft && packId && structureChapters.length === 0 && (
        <section className="sn-glass-card" style={{ padding: 20, marginBottom: 16 }}>
          <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)" }}>
            No chapters yet. Add at least one chapter before approving the pack.
          </p>
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
                      <button
                        type="button"
                        className="sn-btn-ghost"
                        style={btn}
                        onClick={() => approveCard(c.id)}
                        disabled={busy}
                      >
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
                      <button
                        type="button"
                        className="sn-btn-primary"
                        style={btn}
                        onClick={() => approveReview(item.id)}
                        disabled={busy}
                      >
                        Approve
                      </button>
                    )}
                    {item.item_type === "document_ingest" && (
                      <button
                        type="button"
                        className="sn-btn-primary"
                        style={btn}
                        onClick={() => approveReview(item.id)}
                        disabled={busy}
                      >
                        Mark reviewed
                      </button>
                    )}
                    <button
                      type="button"
                      className="sn-btn-ghost"
                      style={{ ...btn, marginLeft: 8 }}
                      onClick={() => rejectReview(item.id)}
                      disabled={busy}
                    >
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
