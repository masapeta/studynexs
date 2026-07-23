"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

type LearningOutcome = { id: string; description: string; code?: string | null };
type PackTopic = {
  id: string;
  title: string;
  concepts?: string[] | null;
  learning_outcomes?: LearningOutcome[];
};
type PackChapter = {
  id: string;
  number?: string | null;
  title: string;
  topics: PackTopic[];
  learning_outcomes?: LearningOutcome[];
};
type PackDetail = {
  id: string;
  class_id: string;
  subject_id: string;
  board: string;
  book_title?: string | null;
  created_by?: string | null;
  chapters: PackChapter[];
};

type Props = {
  packId: string;
  editable?: boolean;
  onStructureChange?: (detail: PackDetail) => void;
};

export function OnboardingReviewPanel({ packId, editable = true, onStructureChange }: Props) {
  const [detail, setDetail] = useState<PackDetail | null>(null);
  const [error, setError] = useState("");
  const [busyTopicId, setBusyTopicId] = useState<string | null>(null);
  const [busyChapterId, setBusyChapterId] = useState<string | null>(null);
  const [busyOutcomeId, setBusyOutcomeId] = useState<string | null>(null);
  const onStructureChangeRef = useRef(onStructureChange);

  useEffect(() => {
    onStructureChangeRef.current = onStructureChange;
  }, [onStructureChange]);

  const load = useCallback(async () => {
    try {
      const r = await api<{ data: PackDetail }>(`/api/v1/curriculum/packs/${packId}`);
      setDetail(r.data);
      onStructureChangeRef.current?.(r.data);
      setError("");
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not load draft pack."));
    }
  }, [packId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function saveTopic(topic: PackTopic, title: string, conceptsText: string) {
    setBusyTopicId(topic.id);
    setError("");
    try {
      const concepts = conceptsText
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean);
      await api(`/api/v1/curriculum/topics/${topic.id}`, {
        method: "PUT",
        body: JSON.stringify({ title: title.trim(), concepts }),
      });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not save topic edits."));
    } finally {
      setBusyTopicId(null);
    }
  }

  async function saveChapter(chapter: PackChapter, number: string, title: string) {
    setBusyChapterId(chapter.id);
    setError("");
    try {
      await api(`/api/v1/curriculum/chapters/${chapter.id}`, {
        method: "PUT",
        body: JSON.stringify({
          number: number.trim() || null,
          title: title.trim(),
        }),
      });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not save chapter edits."));
    } finally {
      setBusyChapterId(null);
    }
  }

  async function removeChapter(chapter: PackChapter) {
    if (!window.confirm(`Remove chapter "${chapter.title}" and its topics?`)) return;
    setBusyChapterId(chapter.id);
    setError("");
    try {
      await api(`/api/v1/curriculum/chapters/${chapter.id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not remove chapter."));
    } finally {
      setBusyChapterId(null);
    }
  }

  async function saveOutcome(outcome: LearningOutcome, description: string) {
    setBusyOutcomeId(outcome.id);
    setError("");
    try {
      await api(`/api/v1/curriculum/learning-outcomes/${outcome.id}`, {
        method: "PUT",
        body: JSON.stringify({ description: description.trim() }),
      });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not save learning outcome."));
    } finally {
      setBusyOutcomeId(null);
    }
  }

  async function removeOutcome(outcome: LearningOutcome) {
    setBusyOutcomeId(outcome.id);
    setError("");
    try {
      await api(`/api/v1/curriculum/learning-outcomes/${outcome.id}`, { method: "DELETE" });
      await load();
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not remove learning outcome."));
    } finally {
      setBusyOutcomeId(null);
    }
  }

  if (error) {
    return (
      <p role="alert" style={{ color: "var(--danger)", fontSize: 13 }}>
        {error}
      </p>
    );
  }
  if (!detail) {
    return <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading proposed structure…</p>;
  }

  const topicCount = detail.chapters.reduce((n, ch) => n + (ch.topics?.length || 0), 0);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <p style={{ margin: 0, fontSize: 13, color: "var(--text-secondary)" }}>
        {detail.chapters.length} chapter(s), {topicCount} topic(s) — correct AI-proposed structure
        before approval.
      </p>
      {detail.chapters.map((chapter) => (
        <article
          key={chapter.id}
          className="sn-workspace-zone"
          style={{ padding: 14, display: "grid", gap: 10 }}
        >
          <ChapterEditor
            chapter={chapter}
            busy={busyChapterId === chapter.id}
            editable={editable}
            onSave={saveChapter}
            onRemove={removeChapter}
          />
          {(chapter.topics || []).length === 0 ? (
            <p style={{ margin: 0, fontSize: 12, color: "var(--warning)" }}>
              No topics yet — add topics in the curriculum builder before approval.
            </p>
          ) : (
            (chapter.topics || []).map((topic) => (
              <TopicEditor
                key={topic.id}
                topic={topic}
                busy={busyTopicId === topic.id}
                editable={editable}
                onSave={saveTopic}
                onSaveOutcome={saveOutcome}
                onRemoveOutcome={removeOutcome}
                busyOutcomeId={busyOutcomeId}
              />
            ))
          )}
          {(chapter.learning_outcomes || []).length > 0 ? (
            <div style={{ display: "grid", gap: 6 }}>
              <p style={{ margin: 0, fontSize: 12, color: "var(--text-muted)" }}>Chapter outcomes</p>
              {(chapter.learning_outcomes || []).map((lo) => (
                <OutcomeEditor
                  key={lo.id}
                  outcome={lo}
                  busy={busyOutcomeId === lo.id}
                  editable={editable}
                  onSave={saveOutcome}
                  onRemove={removeOutcome}
                />
              ))}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function ChapterEditor({
  chapter,
  busy,
  editable,
  onSave,
  onRemove,
}: {
  chapter: PackChapter;
  busy: boolean;
  editable: boolean;
  onSave: (chapter: PackChapter, number: string, title: string) => void | Promise<void>;
  onRemove: (chapter: PackChapter) => void | Promise<void>;
}) {
  const [number, setNumber] = useState(chapter.number || "");
  const [title, setTitle] = useState(chapter.title);

  useEffect(() => {
    setNumber(chapter.number || "");
    setTitle(chapter.title);
  }, [chapter]);

  return (
    <div style={{ display: "grid", gap: 8 }}>
      <div style={{ display: "grid", gridTemplateColumns: "72px 1fr auto auto", gap: 8, alignItems: "center" }}>
        <input
          className="form-input"
          value={number}
          onChange={(e) => setNumber(e.target.value)}
          placeholder="#"
          aria-label={`Chapter number for ${chapter.title}`}
          disabled={busy || !editable}
        />
        <input
          className="form-input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          aria-label={`Chapter title for ${chapter.title}`}
          disabled={busy || !editable}
        />
        <button
          type="button"
          className="sn-btn sn-btn--ghost"
          style={{ width: "auto", padding: "6px 14px", fontSize: 12 }}
          disabled={busy || !editable}
          onClick={() => void onSave(chapter, number, title)}
        >
          {busy ? "Saving…" : "Save chapter"}
        </button>
        <button
          type="button"
          className="sn-btn sn-btn--ghost"
          style={{ width: "auto", padding: "6px 14px", fontSize: 12, color: "var(--danger)" }}
          disabled={busy || !editable}
          onClick={() => void onRemove(chapter)}
        >
          Remove
        </button>
      </div>
    </div>
  );
}

function TopicEditor({
  topic,
  busy,
  editable,
  onSave,
  onSaveOutcome,
  onRemoveOutcome,
  busyOutcomeId,
}: {
  topic: PackTopic;
  busy: boolean;
  editable: boolean;
  onSave: (topic: PackTopic, title: string, concepts: string) => void | Promise<void>;
  onSaveOutcome: (outcome: LearningOutcome, description: string) => void | Promise<void>;
  onRemoveOutcome: (outcome: LearningOutcome) => void | Promise<void>;
  busyOutcomeId: string | null;
}) {
  const [title, setTitle] = useState(topic.title);
  const [concepts, setConcepts] = useState((topic.concepts || []).join(", "));

  useEffect(() => {
    setTitle(topic.title);
    setConcepts((topic.concepts || []).join(", "));
  }, [topic]);

  return (
    <div style={{ display: "grid", gap: 6, paddingLeft: 8, borderLeft: "2px solid var(--border-subtle)" }}>
      <input
        className="form-input"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        aria-label={`Topic title for ${topic.title}`}
        disabled={busy || !editable}
      />
      <input
        className="form-input"
        value={concepts}
        onChange={(e) => setConcepts(e.target.value)}
        placeholder="Concepts (comma-separated)"
        aria-label={`Concepts for ${topic.title}`}
        disabled={busy || !editable}
      />
      {(topic.learning_outcomes || []).length > 0 ? (
        <div style={{ display: "grid", gap: 6 }}>
          {(topic.learning_outcomes || []).map((lo) => (
            <OutcomeEditor
              key={lo.id}
              outcome={lo}
              busy={busyOutcomeId === lo.id}
              editable={editable}
              onSave={onSaveOutcome}
              onRemove={onRemoveOutcome}
            />
          ))}
        </div>
      ) : null}
      <button
        type="button"
        className="sn-btn sn-btn--ghost"
        style={{ width: "auto", padding: "6px 14px", fontSize: 12 }}
        disabled={busy || !editable}
        onClick={() => void onSave(topic, title, concepts)}
      >
        {busy ? "Saving…" : "Save topic"}
      </button>
    </div>
  );
}

function OutcomeEditor({
  outcome,
  busy,
  editable,
  onSave,
  onRemove,
}: {
  outcome: LearningOutcome;
  busy: boolean;
  editable: boolean;
  onSave: (outcome: LearningOutcome, description: string) => void | Promise<void>;
  onRemove: (outcome: LearningOutcome) => void | Promise<void>;
}) {
  const [description, setDescription] = useState(outcome.description);

  useEffect(() => {
    setDescription(outcome.description);
  }, [outcome]);

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: 6, alignItems: "center" }}>
      <input
        className="form-input"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        aria-label="Learning outcome description"
        disabled={busy || !editable}
      />
      <button
        type="button"
        className="sn-btn sn-btn--ghost"
        style={{ width: "auto", padding: "4px 10px", fontSize: 11 }}
        disabled={busy || !editable}
        onClick={() => void onSave(outcome, description)}
      >
        Save
      </button>
      <button
        type="button"
        className="sn-btn sn-btn--ghost"
        style={{ width: "auto", padding: "4px 10px", fontSize: 11, color: "var(--danger)" }}
        disabled={busy || !editable}
        onClick={() => void onRemove(outcome)}
      >
        Remove
      </button>
    </div>
  );
}

export type { PackDetail };
