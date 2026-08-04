"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, CheckCircle2, GraduationCap, Wallet } from "lucide-react";
import { api, getApiErrorMessage } from "@/lib/api";
import { PageHeaderCard } from "@/components/layout/PageHeaderCard";
import { AppSelect } from "@/components/ui/AppSelect";

type YearRow = {
  id: string;
  year_label: string;
  start_date: string;
  is_active: boolean;
};

type ClassRow = {
  id: string;
  grade: string;
  section: string;
  academic_year_id: string;
  student_count?: number;
};

type Candidate = {
  student_id: string;
  student_name: string | null;
  admission_no: string | null;
  roll_no: string | null;
  outcome: string;
  target_class_id: string | null;
  target_class_label: string | null;
  has_unsettled_dues: boolean;
  warnings: string[];
};

type Plan = {
  from_class_id: string;
  from_class_label: string;
  from_year_label: string;
  to_class_id: string;
  to_class_label: string;
  to_year_label: string;
  candidates: Candidate[];
  summary: Record<string, number>;
  enrollments_created?: number | null;
  enrollments_closed?: number | null;
};

type Outcome = "promoted" | "detained" | "graduated";

type Override = { outcome: Outcome; targetClassId: string };

const OUTCOME_BADGE: Record<string, string> = {
  promoted: "badge-success",
  detained: "badge-warning",
  graduated: "badge-info",
  skipped: "badge-warning",
};

function classLabel(c: ClassRow): string {
  return `${c.grade} ${c.section}`;
}

function SummaryChips({ summary }: { summary: Record<string, number> }) {
  const chips: Array<{ key: string; label: string; tone: string }> = [
    { key: "promoted", label: "Promoted", tone: "var(--success)" },
    { key: "detained", label: "Detained", tone: "var(--warning)" },
    { key: "graduated", label: "Graduated", tone: "var(--info)" },
    { key: "skipped", label: "Skipped", tone: "var(--text-muted)" },
    { key: "with_unsettled_dues", label: "With dues", tone: "var(--danger)" },
  ];
  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
      {chips.map((chip) => (
        <div
          key={chip.key}
          className="card"
          style={{ padding: "8px 14px", display: "flex", alignItems: "baseline", gap: 8 }}
        >
          <span style={{ fontSize: 18, fontWeight: 700, color: chip.tone }}>
            {summary[chip.key] ?? 0}
          </span>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{chip.label}</span>
        </div>
      ))}
    </div>
  );
}

export default function PromotePage() {
  const router = useRouter();
  const [years, setYears] = useState<YearRow[]>([]);
  const [classes, setClasses] = useState<ClassRow[]>([]);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);

  const [fromClassId, setFromClassId] = useState("");
  const [toClassId, setToClassId] = useState("");

  const [plan, setPlan] = useState<Plan | null>(null);
  const [overrides, setOverrides] = useState<Record<string, Override>>({});
  const [previewing, setPreviewing] = useState(false);
  const [error, setError] = useState("");

  const [reason, setReason] = useState("");
  const [committing, setCommitting] = useState(false);
  const [result, setResult] = useState<Plan | null>(null);

  useEffect(() => {
    Promise.all([
      api<{ data: YearRow[] }>("/api/v1/school/academic-years"),
      api<{ items: ClassRow[] }>("/api/v1/academic/classes?page_size=100"),
    ])
      .then(([yearsRes, classesRes]) => {
        setYears(yearsRes.data || []);
        setClasses(classesRes.items || []);
      })
      .catch((e) => setLoadError(getApiErrorMessage(e, "Failed to load classes")))
      .finally(() => setLoading(false));
  }, []);

  const yearById = useMemo(() => {
    const map: Record<string, YearRow> = {};
    for (const y of years) map[y.id] = y;
    return map;
  }, [years]);

  const classById = useMemo(() => {
    const map: Record<string, ClassRow> = {};
    for (const c of classes) map[c.id] = c;
    return map;
  }, [classes]);

  const fromClass = classById[fromClassId];
  const fromOptions = useMemo(
    () => [
      { value: "", label: "Select class…" },
      ...classes.map((c) => ({
        value: c.id,
        label: `${classLabel(c)} — ${yearById[c.academic_year_id]?.year_label ?? "?"}`,
      })),
    ],
    [classes, yearById]
  );

  // Target classes: a later academic year than the source class.
  const toOptions = useMemo(() => {
    if (!fromClass) return [{ value: "", label: "Pick the current class first" }];
    const fromYear = yearById[fromClass.academic_year_id];
    const later = classes.filter((c) => {
      const year = yearById[c.academic_year_id];
      return year && fromYear && year.start_date > fromYear.start_date;
    });
    if (later.length === 0) {
      return [{ value: "", label: "No classes exist in a later academic year yet" }];
    }
    return [
      { value: "", label: "Select class…" },
      ...later.map((c) => ({
        value: c.id,
        label: `${classLabel(c)} — ${yearById[c.academic_year_id]?.year_label ?? "?"}`,
      })),
    ];
  }, [classes, fromClass, yearById]);

  // Classes a detained student can repeat in: the target year only.
  const repeatOptions = useMemo(() => {
    const toClass = classById[toClassId];
    if (!toClass) return [];
    return [
      { value: "", label: "Repeat class…" },
      ...classes
        .filter((c) => c.academic_year_id === toClass.academic_year_id)
        .map((c) => ({ value: c.id, label: classLabel(c) })),
    ];
  }, [classes, classById, toClassId]);

  function buildExclusions() {
    return Object.entries(overrides)
      .filter(([, o]) => o.outcome !== "promoted")
      .map(([studentId, o]) => ({
        student_id: studentId,
        outcome: o.outcome,
        target_class_id: o.outcome === "detained" && o.targetClassId ? o.targetClassId : null,
      }));
  }

  async function runPreview(exclusions = buildExclusions()) {
    setPreviewing(true);
    setError("");
    try {
      const res = await api<{ data: Plan }>("/api/v1/academic/enrollments/promote/preview", {
        method: "POST",
        body: JSON.stringify({
          from_class_id: fromClassId,
          to_class_id: toClassId,
          exclusions,
        }),
      });
      setPlan(res.data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Could not build the promotion plan"));
    } finally {
      setPreviewing(false);
    }
  }

  function startPreview() {
    setOverrides({});
    setResult(null);
    setReason("");
    void runPreview([]);
  }

  function setOutcome(studentId: string, outcome: Outcome) {
    setOverrides((prev) => {
      const next = { ...prev };
      if (outcome === "promoted") delete next[studentId];
      else next[studentId] = { outcome, targetClassId: prev[studentId]?.targetClassId ?? "" };
      return next;
    });
  }

  function setRepeatClass(studentId: string, targetClassId: string) {
    setOverrides((prev) => ({
      ...prev,
      [studentId]: { outcome: "detained", targetClassId },
    }));
  }

  // Local view of the plan with the admin's pending outcome choices applied.
  const viewCandidates = useMemo(() => {
    if (!plan) return [];
    return plan.candidates.map((c) => {
      if (c.outcome === "skipped") return c;
      const override = overrides[c.student_id];
      if (!override) return { ...c, outcome: "promoted" as string };
      return { ...c, outcome: override.outcome };
    });
  }, [plan, overrides]);

  const viewSummary = useMemo(() => {
    const summary: Record<string, number> = {
      promoted: 0,
      detained: 0,
      graduated: 0,
      skipped: 0,
      with_unsettled_dues: 0,
      total: viewCandidates.length,
    };
    for (const c of viewCandidates) {
      summary[c.outcome] = (summary[c.outcome] ?? 0) + 1;
      if (c.has_unsettled_dues && c.outcome !== "skipped") summary.with_unsettled_dues += 1;
    }
    return summary;
  }, [viewCandidates]);

  const detainedWithoutClass = useMemo(
    () =>
      Object.values(overrides).some((o) => o.outcome === "detained" && !o.targetClassId),
    [overrides]
  );

  async function commit() {
    if (reason.trim().length < 3) {
      setError("Give a reason — it is recorded in the audit trail.");
      return;
    }
    if (detainedWithoutClass) {
      setError("Every detained student needs a class to repeat in.");
      return;
    }
    setCommitting(true);
    setError("");
    try {
      const res = await api<{ data: Plan }>("/api/v1/academic/enrollments/promote", {
        method: "POST",
        body: JSON.stringify({
          from_class_id: fromClassId,
          to_class_id: toClassId,
          exclusions: buildExclusions(),
          reason: reason.trim(),
        }),
      });
      setResult(res.data);
    } catch (e) {
      setError(getApiErrorMessage(e, "Promotion failed — nothing was changed"));
    } finally {
      setCommitting(false);
    }
  }

  if (loading) {
    return (
      <div className="loading-screen" style={{ minHeight: "50vh" }}>
        <div className="spinner" />
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="card" style={{ padding: 32, textAlign: "center" }}>
        <p style={{ color: "var(--danger)", marginBottom: 16 }}>{loadError}</p>
        <button type="button" className="btn btn-outline" onClick={() => router.push("/dashboard/classes")}>
          Back to classes
        </button>
      </div>
    );
  }

  return (
    <>
      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => router.push("/dashboard/classes")}
        style={{ width: "auto", padding: "6px 0", marginBottom: 16, display: "flex", alignItems: "center", gap: 6 }}
      >
        <ArrowLeft size={16} /> Back to classes
      </button>

      <PageHeaderCard
        title="Promotion & year rollover"
        subtitle="Move a class into the next academic year. Preview first — nothing changes until you commit."
      />

      {/* Step 1: pick classes */}
      <div
        className="card sn-section-gap"
        style={{ padding: 18, display: "grid", gridTemplateColumns: "1fr auto 1fr auto", gap: 14, alignItems: "end" }}
      >
        <div>
          <label className="stat-label">Current class (this year)</label>
          <AppSelect
            variant="field"
            value={fromClassId}
            onChange={(v) => {
              setFromClassId(v);
              setToClassId("");
              setPlan(null);
              setResult(null);
            }}
            aria-label="Class to promote"
            options={fromOptions}
          />
        </div>
        <ArrowRight size={18} style={{ color: "var(--text-muted)", marginBottom: 12 }} />
        <div>
          <label className="stat-label">Target class (next year)</label>
          <AppSelect
            variant="field"
            value={toClassId}
            onChange={(v) => {
              setToClassId(v);
              setPlan(null);
              setResult(null);
            }}
            aria-label="Class to promote into"
            options={toOptions}
          />
        </div>
        <button
          type="button"
          className="btn btn-primary"
          style={{ width: "auto", padding: "10px 20px" }}
          onClick={startPreview}
          disabled={!fromClassId || !toClassId || previewing}
        >
          {previewing ? "Building plan…" : "Preview promotion"}
        </button>
      </div>

      {error && (
        <div className="card sn-section-gap" style={{ padding: 12, color: "var(--danger)" }} role="alert">
          {error}
        </div>
      )}

      {/* Committed result */}
      {result && (
        <div className="card sn-section-gap" style={{ padding: 18 }} role="status">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <CheckCircle2 size={20} style={{ color: "var(--success)" }} />
            <strong>
              Rollover complete — {result.enrollments_closed ?? 0} enrollment(s) closed,{" "}
              {result.enrollments_created ?? 0} opened in {result.to_year_label}.
            </strong>
          </div>
          <SummaryChips summary={result.summary} />
          <div style={{ marginTop: 14, display: "flex", gap: 10 }}>
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: "auto", padding: "8px 18px" }}
              onClick={() => {
                setFromClassId("");
                setToClassId("");
                setPlan(null);
                setResult(null);
                setOverrides({});
                setReason("");
              }}
            >
              Promote another class
            </button>
            <button
              type="button"
              className="btn btn-outline"
              style={{ width: "auto", padding: "8px 18px" }}
              onClick={() => router.push("/dashboard/classes")}
            >
              Back to classes
            </button>
          </div>
        </div>
      )}

      {/* Step 2: the plan */}
      {plan && !result && (
        <>
          <div className="card sn-section-gap" style={{ padding: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14, flexWrap: "wrap" }}>
              <GraduationCap size={18} style={{ color: "var(--accent)" }} />
              <strong>
                {plan.from_class_label} ({plan.from_year_label}) → {plan.to_class_label} (
                {plan.to_year_label})
              </strong>
            </div>
            <SummaryChips summary={viewSummary} />
            {viewSummary.with_unsettled_dues > 0 && (
              <p style={{ margin: "12px 0 0", fontSize: 13, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 6 }}>
                <Wallet size={14} />
                Unpaid dues carry over unchanged — promotion never edits what a family owes.
              </p>
            )}
          </div>

          <div className="data-table-card sn-section-gap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Roll</th>
                  <th>Student</th>
                  <th>Outcome</th>
                  <th>Goes to</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {viewCandidates.length === 0 ? (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: 40, color: "var(--text-muted)" }}>
                      No students found in this class&rsquo;s enrollment roster.
                    </td>
                  </tr>
                ) : (
                  viewCandidates.map((c) => {
                    const skipped = plan.candidates.find(
                      (raw) => raw.student_id === c.student_id
                    )?.outcome === "skipped";
                    const override = overrides[c.student_id];
                    return (
                      <tr key={c.student_id}>
                        <td>{c.roll_no || "—"}</td>
                        <td>
                          <div style={{ fontWeight: 600 }}>{c.student_name || "—"}</div>
                          <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                            {c.admission_no || ""}
                          </div>
                        </td>
                        <td>
                          {skipped ? (
                            <span className={`badge ${OUTCOME_BADGE.skipped}`}>skipped</span>
                          ) : (
                            <AppSelect
                              value={c.outcome}
                              onChange={(v) => setOutcome(c.student_id, v as Outcome)}
                              aria-label={`Outcome for ${c.student_name || c.admission_no}`}
                              options={[
                                { value: "promoted", label: "Promote" },
                                { value: "detained", label: "Detain (repeat year)" },
                                { value: "graduated", label: "Graduate (leaves school)" },
                              ]}
                            />
                          )}
                        </td>
                        <td>
                          {skipped ? (
                            "—"
                          ) : c.outcome === "detained" ? (
                            <AppSelect
                              value={override?.targetClassId ?? ""}
                              onChange={(v) => setRepeatClass(c.student_id, v)}
                              aria-label={`Repeat class for ${c.student_name || c.admission_no}`}
                              options={repeatOptions}
                            />
                          ) : c.outcome === "graduated" ? (
                            <span style={{ color: "var(--text-muted)" }}>Alumni</span>
                          ) : (
                            plan.to_class_label
                          )}
                        </td>
                        <td style={{ fontSize: 12, color: "var(--text-muted)" }}>
                          {c.has_unsettled_dues && (
                            <span className="badge badge-warning" style={{ marginRight: 6 }}>
                              dues
                            </span>
                          )}
                          {c.warnings.join(" · ")}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Step 3: commit */}
          <div className="card sn-section-gap" style={{ padding: 18 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 14, alignItems: "end" }}>
              <div>
                <label className="stat-label" htmlFor="promotion-reason">
                  Reason (recorded in the audit trail)
                </label>
                <input
                  id="promotion-reason"
                  className="form-input sn-inline-field"
                  value={reason}
                  placeholder={`Annual rollover ${plan.to_year_label}`}
                  onChange={(e) => setReason(e.target.value)}
                />
              </div>
              <button
                type="button"
                className="btn btn-primary"
                style={{ width: "auto", padding: "10px 22px" }}
                onClick={commit}
                disabled={committing || viewCandidates.length === 0}
              >
                {committing
                  ? "Promoting…"
                  : `Commit — promote ${viewSummary.promoted}, detain ${viewSummary.detained}, graduate ${viewSummary.graduated}`}
              </button>
            </div>
            {detainedWithoutClass && (
              <p style={{ margin: "10px 0 0", fontSize: 13, color: "var(--warning)" }}>
                Every detained student needs a repeat class before you can commit.
              </p>
            )}
            <p style={{ margin: "10px 0 0", fontSize: 12, color: "var(--text-muted)" }}>
              This closes each student&rsquo;s {plan.from_year_label} enrollment and opens{" "}
              {plan.to_year_label}. Past attendance, marks, and receipts stay with{" "}
              {plan.from_class_label}. There is no bulk undo — check the plan above first.
            </p>
          </div>
        </>
      )}
    </>
  );
}
