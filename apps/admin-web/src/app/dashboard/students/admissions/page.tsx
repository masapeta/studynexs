"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { FilterPillBar } from "@/components/layout/FilterPillBar";
import { PersonMono } from "@/components/briefing/PersonMono";
import { StatusBadge } from "@/components/briefing/StatusBadge";
import {
  AdmissionEnquiryModal,
  type EnquiryFormData,
} from "@/components/admissions/AdmissionEnquiryModal";
import { AdmissionDetailModal } from "@/components/admissions/AdmissionDetailModal";
import { AdmissionStageFormModal } from "@/components/admissions/AdmissionStageFormModal";
import {
  STAGES,
  type Stage,
  type StageFormTarget,
  canMoveToStage,
  needsStageForm,
} from "@/components/admissions/stage-forms";
import {
  type AdmissionCandidate,
  formatAdmissionDate,
  stageLabel,
} from "@/components/admissions/types";
import { ChevronLeft, ChevronRight, UserPlus } from "lucide-react";
import { AppSelect } from "@/components/ui/AppSelect";

const stageTone: Record<string, "brass" | "blue" | "gray" | "green"> = {
  enquiry: "brass",
  applied: "blue",
  interview: "brass",
  offer: "blue",
  enrolled: "green",
};

function formatEnquiry(iso: string) {
  return formatAdmissionDate(iso);
}

function pipelineFromCandidates(list: AdmissionCandidate[]): Record<string, number> {
  const counts = Object.fromEntries(STAGES.map((s) => [s, 0])) as Record<string, number>;
  for (const c of list) {
    if (c.stage in counts) counts[c.stage] += 1;
  }
  return counts;
}

function buildEnquiryPayload(form: EnquiryFormData) {
  return {
    name: form.name.trim(),
    grade_applied: form.grade_applied.trim(),
    enquiry_date: form.enquiry_date,
    date_of_birth: form.date_of_birth || null,
    gender: form.gender || null,
    parent_name: form.parent_name.trim(),
    parent_relation: form.parent_relation,
    parent_occupation: form.parent_occupation.trim() || null,
    parent_mobile: form.parent_mobile.trim(),
    parent_email: form.parent_email.trim() || null,
    address_line: form.address_line.trim() || null,
    city: form.city.trim() || null,
    previous_school_name: form.previous_school_name.trim() || null,
    previous_grade: form.previous_grade.trim() || null,
    enquiry_source: form.enquiry_source || null,
    notes: form.notes.trim() || null,
  };
}

export default function AdmissionsPage() {
  const [candidates, setCandidates] = useState<AdmissionCandidate[]>([]);
  const [pipeline, setPipeline] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [viewCandidate, setViewCandidate] = useState<AdmissionCandidate | null>(null);
  const [modalError, setModalError] = useState("");
  const [saving, setSaving] = useState(false);
  const [stageForm, setStageForm] = useState<{
    candidate: AdmissionCandidate;
    targetStage: StageFormTarget;
  } | null>(null);
  const [stageFormError, setStageFormError] = useState("");
  const [stageSaving, setStageSaving] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [stageFilter, setStageFilter] = useState<Stage | null>(null);
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const filteredCandidates = useMemo(() => {
    let list = candidates;
    if (stageFilter) {
      list = list.filter((c) => c.stage === stageFilter);
    }
    const q = searchQuery.trim().toLowerCase();
    if (!q) return list;
    return list.filter((c) => c.name.toLowerCase().includes(q));
  }, [candidates, searchQuery, stageFilter]);

  const totalCandidates = candidates.length;

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true);
    setError("");
    try {
      const res = await api<{ data: { candidates: AdmissionCandidate[]; pipeline: Record<string, number> } }>(
        "/api/v1/ops/admissions"
      );
      setCandidates(res.data?.candidates || []);
      setPipeline(res.data?.pipeline || {});
    } catch (e) {
      setError(getApiErrorMessage(e, "Failed to load admissions"));
    } finally {
      if (!opts?.silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (highlightTimer.current) clearTimeout(highlightTimer.current);
    };
  }, []);

  function flashRow(id: string) {
    if (highlightTimer.current) clearTimeout(highlightTimer.current);
    setHighlightedId(id);
    highlightTimer.current = setTimeout(() => setHighlightedId(null), 1800);
  }

  useEffect(() => {
    load();
  }, [load]);

  async function addEnquiry(form: EnquiryFormData) {
    setSaving(true);
    setModalError("");
    try {
      const res = await api<{ data: { id: string } }>("/api/v1/ops/admissions", {
        method: "POST",
        body: JSON.stringify(buildEnquiryPayload(form)),
      });
      setModalOpen(false);
      await load({ silent: true });
      if (res.data?.id) flashRow(res.data.id);
    } catch (e) {
      setModalError(getApiErrorMessage(e, "Could not add enquiry"));
    } finally {
      setSaving(false);
    }
  }

  const commitStageChange = useCallback(
    async (
      candidate: AdmissionCandidate,
      targetStage: Stage,
      details?: Record<string, unknown>
    ) => {
      const previousStage = candidate.stage;
      const previousDetails = candidate.stage_details;

      const nextDetails = details
        ? {
            ...(candidate.stage_details || {}),
            [targetStage]: details,
          }
        : candidate.stage_details;

      const identityPatch =
        targetStage === "applied" && details
          ? {
              aadhaar_number: details.aadhaar_number
                ? String(details.aadhaar_number)
                : candidate.aadhaar_number,
              birth_certificate_number: details.birth_certificate_number
                ? String(details.birth_certificate_number)
                : candidate.birth_certificate_number,
              apaar_number: details.apaar_number
                ? String(details.apaar_number)
                : candidate.apaar_number,
            }
          : {};

      setCandidates((list) => {
        const next = list.map((c) =>
          c.id === candidate.id
            ? {
                ...c,
                stage: targetStage,
                stage_details: nextDetails,
                ...identityPatch,
              }
            : c
        );
        setPipeline(pipelineFromCandidates(next));
        return next;
      });
      flashRow(candidate.id);
      setUpdatingId(candidate.id);
      setError("");

      try {
        await api(`/api/v1/ops/admissions/${candidate.id}/stage`, {
          method: "PATCH",
          body: JSON.stringify({
            stage: targetStage,
            ...(details ? { details } : {}),
          }),
        });
        setViewCandidate((current) =>
          current?.id === candidate.id
            ? {
                ...current,
                stage: targetStage,
                stage_details: nextDetails,
                ...identityPatch,
              }
            : current
        );
      } catch (e) {
        setCandidates((list) => {
          const next = list.map((c) =>
            c.id === candidate.id
              ? { ...c, stage: previousStage, stage_details: previousDetails }
              : c
          );
          setPipeline(pipelineFromCandidates(next));
          return next;
        });
        setHighlightedId(null);
        const message = getApiErrorMessage(e, "Could not update stage");
        setError(message);
        throw new Error(message);
      } finally {
        setUpdatingId(null);
      }
    },
    []
  );

  function requestStageChange(candidate: AdmissionCandidate, targetStage: Stage) {
    if (candidate.stage === targetStage) return;
    const from = candidate.stage as Stage;
    if (!canMoveToStage(from, targetStage)) {
      setError("Move one stage at a time — enquiry → applied → interview → offer → enrolled.");
      return;
    }
    if (needsStageForm(candidate, targetStage)) {
      setStageFormError("");
      setStageForm({ candidate, targetStage });
      return;
    }
    void commitStageChange(candidate, targetStage);
  }

  async function submitStageForm(details: Record<string, unknown>) {
    if (!stageForm) return;
    setStageSaving(true);
    setStageFormError("");
    try {
      await commitStageChange(stageForm.candidate, stageForm.targetStage, details);
      setStageForm(null);
    } catch (e) {
      setStageFormError(getApiErrorMessage(e, "Could not save stage details"));
    } finally {
      setStageSaving(false);
    }
  }

  function stepStage(candidate: AdmissionCandidate, direction: "forward" | "back") {
    const idx = STAGES.indexOf(candidate.stage as Stage);
    if (idx < 0) return;
    const next = direction === "forward" ? STAGES[idx + 1] : STAGES[idx - 1];
    if (!next) return;
    requestStageChange(candidate, next);
  }

  return (
    <>
      <PageHeaderCard
        title="Admissions"
        subtitle="Record new enquiries and move candidates through the pipeline."
      >
        <input
          className="form-input sn-search-inline"
          placeholder="Search candidates..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label="Search candidates by name"
        />
        <button
          type="button"
          className="gw-table-icon-btn"
          aria-label="Add enquiry"
          title="Add enquiry"
          onClick={() => setModalOpen(true)}
        >
          <UserPlus size={20} />
        </button>
      </PageHeaderCard>

      {error && (
        <div className="card" style={{ marginBottom: 16, padding: 12, color: "var(--danger)" }}>
          {error}
        </div>
      )}

      <FilterPillBar
        tabs={[
          { key: "all", label: "Total Enquiries", count: totalCandidates },
          ...STAGES.map((stage) => ({
            key: stage,
            label: stageLabel(stage),
            count: pipeline[stage] ?? 0,
          })),
        ]}
        activeKey={stageFilter ?? "all"}
        onChange={(key) => setStageFilter(key === "all" ? null : (key as Stage))}
        ariaLabel="Filter by admission stage"
      />

      <div className="gw-card gw-card-pad">
        {loading ? (
          <div className="gw-center"><div className="spinner" /></div>
        ) : candidates.length === 0 ? (
          <div className="gw-empty-state">
            <p className="gw-muted">No candidates in the pipeline yet.</p>
            {!modalOpen && (
              <button
                type="button"
                className="gw-table-icon-btn"
                aria-label="Record first enquiry"
                title="Record first enquiry"
                onClick={() => setModalOpen(true)}
              >
                <UserPlus size={20} />
              </button>
            )}
          </div>
        ) : filteredCandidates.length === 0 ? (
          <p className="gw-muted">
            {searchQuery.trim() && stageFilter
              ? `No ${stageLabel(stageFilter).toLowerCase()} candidates match "${searchQuery.trim()}".`
              : searchQuery.trim()
                ? `No candidates match "${searchQuery.trim()}".`
                : stageFilter
                  ? `No candidates in ${stageLabel(stageFilter).toLowerCase()} yet.`
                  : "No candidates match your filters."}
          </p>
        ) : (
          <ul className="gw-list">
            {filteredCandidates.map((c) => {
              const stageIdx = STAGES.indexOf(c.stage as Stage);
              const canBack = stageIdx > 0;
              const canForward = stageIdx >= 0 && stageIdx < STAGES.length - 1;
              const busy = updatingId === c.id;
              const metaParts = [
                `Grade ${c.grade_applied}`,
                `enquiry ${formatEnquiry(c.enquiry_date)}`,
              ];
              if (c.parent_name) metaParts.push(`parent: ${c.parent_name}`);
              if (c.previous_school_name) metaParts.push(`from ${c.previous_school_name}`);

              return (
                <li
                  key={c.id}
                  className={`gw-list-row gw-admission-row${highlightedId === c.id ? " gw-admission-row-flash" : ""}${busy ? " gw-admission-row-busy" : ""}`}
                >
                  <button
                    type="button"
                    className="gw-admission-row-main"
                    onClick={() => setViewCandidate(c)}
                    aria-label={`View enquiry for ${c.name}`}
                  >
                    <PersonMono name={c.name} size={36} />
                    <div className="gw-list-main">
                      <div className="gw-list-title">{c.name}</div>
                      <div className="gw-list-meta">{metaParts.join(" · ")}</div>
                    </div>
                  </button>
                  <div
                    className="gw-admission-stage-controls"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      className="btn btn-ghost gw-btn-sm gw-stage-step"
                      disabled={!canBack || busy}
                      title="Move to previous stage"
                      onClick={() => stepStage(c, "back")}
                    >
                      <ChevronLeft size={16} />
                    </button>
                    <AppSelect
                      variant="field"
                      className="gw-stage-select"
                      value={c.stage}
                      disabled={busy}
                      onChange={(v) => requestStageChange(c, v as Stage)}
                      aria-label={`Stage for ${c.name}`}
                      options={STAGES.map((stage) => ({
                        value: stage,
                        label: stageLabel(stage),
                        disabled: stage !== c.stage && !canMoveToStage(c.stage as Stage, stage),
                      }))}
                    />
                    <button
                      type="button"
                      className="btn btn-ghost gw-btn-sm gw-stage-step"
                      disabled={!canForward || busy}
                      title="Move to next stage"
                      onClick={() => stepStage(c, "forward")}
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                  <StatusBadge tone={stageTone[c.stage] || "gray"}>
                    {stageLabel(c.stage)}
                  </StatusBadge>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <AdmissionEnquiryModal
        open={modalOpen}
        saving={saving}
        error={modalError}
        onClose={() => !saving && setModalOpen(false)}
        onSubmit={addEnquiry}
      />

      <AdmissionStageFormModal
        candidate={stageForm?.candidate ?? null}
        targetStage={stageForm?.targetStage ?? null}
        saving={stageSaving}
        error={stageFormError}
        onClose={() => !stageSaving && setStageForm(null)}
        onSubmit={submitStageForm}
      />

      <AdmissionDetailModal
        candidate={viewCandidate}
        onClose={() => setViewCandidate(null)}
      />
    </>
  );
}
