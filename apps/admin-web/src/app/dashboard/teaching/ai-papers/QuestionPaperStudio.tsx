"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  LayoutTemplate,
  Network,
  Plus,
  Settings2,
  ShieldAlert,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AcademicIntelligenceBanner } from "@/components/curriculum/AcademicIntelligenceBanner";
import { AppSelect } from "@/components/ui/AppSelect";
import { api } from "@/lib/api";
import { AI_INPUT, parseTopicList } from "@/lib/ai-input-limits";
import { TEACHING } from "@/lib/dashboard-routes";
import { formatClassLabel } from "@/lib/format";
import {
  BLOOM_OPTIONS,
  BlueprintSlot,
  EXAM_TYPE_OPTIONS,
  ExamType,
  QUESTION_TYPE_OPTIONS,
  SectionPlanItem,
  buildBlueprintSlots,
  buildDefaultSectionPlan,
  distributeByWeight,
  distributeTotal,
  sumSectionPlan,
  validateSectionPlan,
} from "@/lib/question-paper-studio";
import styles from "./studio.module.css";

export type StudioClass = { id: string; grade: string; section: string };
export type StudioSubject = { id: string; name: string };
export type StudioPack = { id: string; status: string; board: string; book_title?: string | null };

type PackChapter = { id: string; number?: string | null; title: string };
type PackDetail = StudioPack & { chapters: PackChapter[] };

export type StudioGenerateRequest = {
  mode: "full" | "from_bank";
  class_id: string;
  subject_id: string;
  topics: string[];
  total_marks: number;
  duration_minutes: number;
  difficulty: string;
  exam_type: ExamType;
  title: string;
  pack_id?: string;
  ungrounded_acknowledged?: boolean;
  ungrounded_reason?: string;
  section_plan: SectionPlanItem[];
  blueprint_slots: BlueprintSlot[];
};

type Props = {
  classes: StudioClass[];
  subjects: StudioSubject[];
  classId: string;
  subjectId: string;
  onClassChange: (value: string) => void;
  onSubjectChange: (value: string) => void;
  packs: StudioPack[];
  packId: string;
  onPackChange: (value: string) => void;
  bankCount: number | null;
  fullCost: number;
  bankCost: number;
  initialTopics: string;
  initialDifficulty: string;
  initialGrounding: boolean;
  canEditCurriculum: boolean;
  canGenerateUngrounded: boolean;
  generating: boolean;
  error: string;
  onGenerate: (request: StudioGenerateRequest) => Promise<void>;
};

const DEFAULT_BLOOM_WEIGHTS = {
  remember: 20,
  understand: 20,
  apply: 30,
  analyse: 30,
};

function chapterLabel(chapter: PackChapter): string {
  return chapter.number ? `${chapter.number}. ${chapter.title}` : chapter.title;
}

function looseTopicLabels(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 20);
}

export function QuestionPaperStudio({
  classes,
  subjects,
  classId,
  subjectId,
  onClassChange,
  onSubjectChange,
  packs,
  packId,
  onPackChange,
  bankCount,
  fullCost,
  bankCost,
  initialTopics,
  initialDifficulty,
  initialGrounding,
  canEditCurriculum,
  canGenerateUngrounded,
  generating,
  error,
  onGenerate,
}: Props) {
  const [step, setStep] = useState(1);
  const [examName, setExamName] = useState("Unit Test");
  const [examType, setExamType] = useState<ExamType>("unit_test");
  const [topics, setTopics] = useState(initialTopics);
  const [totalMarks, setTotalMarks] = useState(40);
  const [duration, setDuration] = useState(90);
  const [difficulty, setDifficulty] = useState(initialDifficulty || "balanced");
  const [generateMode, setGenerateMode] = useState<"full" | "from_bank">("full");
  const [useGrounding, setUseGrounding] = useState(
    initialGrounding || !canGenerateUngrounded
  );
  const [ungroundedAcknowledged, setUngroundedAcknowledged] = useState(false);
  const [ungroundedReason, setUngroundedReason] = useState("");
  const [scopeMode, setScopeMode] = useState<"multiple" | "single">("multiple");
  const [packDetail, setPackDetail] = useState<PackDetail | null>(null);
  const [packLoadFailed, setPackLoadFailed] = useState(false);
  const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
  const [chapterMarks, setChapterMarks] = useState<Record<string, number>>(() =>
    distributeTotal(looseTopicLabels(initialTopics), 40)
  );
  const [bloomWeights, setBloomWeights] = useState<Record<string, number>>(DEFAULT_BLOOM_WEIGHTS);
  const [sectionPlan, setSectionPlan] = useState<SectionPlanItem[]>(() =>
    buildDefaultSectionPlan(40)
  );
  const [blueprintSlots, setBlueprintSlots] = useState<BlueprintSlot[]>([]);
  const [localError, setLocalError] = useState("");
  const totalMarksRef = useRef(totalMarks);

  const freeTopicLabels = useMemo(() => looseTopicLabels(topics), [topics]);
  const groundedScope = useGrounding && generateMode === "full";
  const chapterLabelsById = useMemo(
    () => Object.fromEntries(
      (packDetail?.chapters ?? []).map((chapter) => [chapter.id, chapterLabel(chapter)])
    ),
    [packDetail]
  );
  const scopeKeys = groundedScope ? selectedChapters : freeTopicLabels;
  const scopeLabels = scopeKeys.map((key) => chapterLabelsById[key] ?? key);
  const chapterTotal = Object.values(chapterMarks).reduce((sum, value) => sum + Number(value || 0), 0);
  const bloomTotal = Object.values(bloomWeights).reduce((sum, value) => sum + Number(value || 0), 0);
  const templateTotal = sumSectionPlan(sectionPlan);
  const questionCount = sectionPlan.reduce((sum, item) => sum + item.question_count, 0);
  const packLoading = Boolean(
    packId &&
      useGrounding &&
      generateMode === "full" &&
      packDetail?.id !== packId &&
      !packLoadFailed
  );

  useEffect(() => {
    if (!packId || !useGrounding || generateMode !== "full") return;
    let cancelled = false;
    api<PackDetail | { data: PackDetail }>(`/api/v1/curriculum/packs/${packId}`)
      .then((response) => {
        if (cancelled) return;
        const detail = "data" in response ? response.data : response;
        setPackLoadFailed(false);
        setPackDetail(detail);
        const initial = detail.chapters
          .slice(0, Math.min(3, detail.chapters.length))
          .map((chapter) => chapter.id);
        setSelectedChapters(initial);
        setChapterMarks(distributeTotal(initial, totalMarksRef.current));
        setBlueprintSlots([]);
      })
      .catch(() => {
        if (!cancelled) {
          setPackLoadFailed(true);
          setPackDetail(null);
          setSelectedChapters([]);
          setChapterMarks({});
        }
      });
    return () => {
      cancelled = true;
    };
  }, [generateMode, packId, useGrounding]);

  function changeTotalMarks(next: number) {
    totalMarksRef.current = next;
    setTotalMarks(next);
    setSectionPlan(buildDefaultSectionPlan(next));
    setChapterMarks(distributeTotal(scopeKeys, next));
    setBlueprintSlots([]);
  }

  function changeTopics(next: string) {
    setTopics(next);
    setChapterMarks(distributeTotal(looseTopicLabels(next), totalMarks));
    setBlueprintSlots([]);
  }

  function changeGenerateMode(next: "full" | "from_bank") {
    setGenerateMode(next);
    setPackLoadFailed(false);
    setBlueprintSlots([]);
    if (next === "from_bank") {
      setPackDetail(null);
      setChapterMarks(distributeTotal(freeTopicLabels, totalMarks));
    }
  }

  function changeGrounding(next: boolean) {
    if (!next && !canGenerateUngrounded) return;
    setUseGrounding(next);
    setUngroundedAcknowledged(false);
    setUngroundedReason("");
    setPackLoadFailed(false);
    setBlueprintSlots([]);
    if (!next) {
      setPackDetail(null);
      setChapterMarks(distributeTotal(freeTopicLabels, totalMarks));
    }
  }

  function changePack(next: string) {
    setPackLoadFailed(false);
    setPackDetail(null);
    setSelectedChapters([]);
    setChapterMarks({});
    setBlueprintSlots([]);
    onPackChange(next);
  }

  function updateSelectedChapters(next: string[]) {
    const bounded = scopeMode === "single" ? next.slice(-1) : next;
    setSelectedChapters(bounded);
    setChapterMarks(distributeTotal(bounded, totalMarks));
    setBlueprintSlots([]);
  }

  function selectScopeMode(next: "multiple" | "single") {
    setScopeMode(next);
    if (next === "single" && selectedChapters.length > 1) {
      updateSelectedChapters([selectedChapters[0]]);
    }
  }

  function configurationError(): string | null {
    if (!classId || !subjectId) return "Select a class and subject.";
    if (!examName.trim()) return "Enter an examination name.";
    if (!Number.isInteger(totalMarks) || totalMarks < 1 || totalMarks > 200) {
      return "Total marks must be a whole number from 1 to 200.";
    }
    if (!Number.isInteger(duration) || duration < 15 || duration > 360) {
      return "Duration must be a whole number from 15 to 360 minutes.";
    }
    if (useGrounding && generateMode === "full" && !packId) {
      return "Select an approved curriculum pack.";
    }
    if (!useGrounding && generateMode === "full") {
      if (!canGenerateUngrounded) return "An approved curriculum pack is required.";
      if (!ungroundedAcknowledged) {
        return "Acknowledge that this ungrounded draft requires explicit manual review.";
      }
      if (ungroundedReason.trim().length < 10) {
        return "Record a reason of at least 10 characters for the ungrounded exception.";
      }
    }
    if (scopeLabels.length === 0) return "Select at least one chapter or enter one topic.";
    if (chapterTotal !== totalMarks) {
      return `Chapter distribution is ${chapterTotal}; it must equal ${totalMarks} marks.`;
    }
    if (bloomTotal !== 100) return `Objective distribution is ${bloomTotal}%; it must equal 100%.`;
    return null;
  }

  function continueToTemplate() {
    const issue = configurationError();
    if (issue) {
      setLocalError(issue);
      return;
    }
    setLocalError("");
    setStep(2);
  }

  function continueToBlueprint() {
    const issue = validateSectionPlan(sectionPlan, totalMarks);
    if (issue) {
      setLocalError(issue);
      return;
    }
    const bloomMarks = distributeByWeight(bloomWeights, totalMarks);
    const slots = buildBlueprintSlots(sectionPlan, chapterMarks, bloomMarks).map((slot) => (
      groundedScope
        ? {
            ...slot,
            chapter_id: slot.chapter,
            chapter: chapterLabelsById[slot.chapter] ?? slot.chapter,
          }
        : slot
    ));
    setBlueprintSlots(slots);
    setLocalError("");
    setStep(3);
  }

  function updatePlan(index: number, patch: Partial<SectionPlanItem>) {
    setSectionPlan((current) =>
      current.map((item, itemIndex) => (itemIndex === index ? { ...item, ...patch } : item))
    );
    setBlueprintSlots([]);
  }

  async function submitGeneration() {
    const configIssue = configurationError();
    const planIssue = validateSectionPlan(sectionPlan, totalMarks);
    if (configIssue || planIssue || blueprintSlots.length !== questionCount) {
      setLocalError(configIssue || planIssue || "Rebuild the blueprint before generating.");
      return;
    }
    let topicList: string[];
    try {
      topicList = groundedScope ? scopeLabels : parseTopicList(topics);
    } catch (caught) {
      setLocalError(caught instanceof Error ? caught.message : "Invalid topics.");
      return;
    }
    setLocalError("");
    await onGenerate({
      mode: generateMode,
      class_id: classId,
      subject_id: subjectId,
      topics: topicList,
      total_marks: totalMarks,
      duration_minutes: duration,
      difficulty,
      exam_type: examType,
      title: examName.trim(),
      ...(useGrounding && generateMode === "full" && packId ? { pack_id: packId } : {}),
      ...(!useGrounding && generateMode === "full"
        ? {
            ungrounded_acknowledged: true,
            ungrounded_reason: ungroundedReason.trim(),
          }
        : {}),
      section_plan: sectionPlan,
      blueprint_slots:
        generateMode === "from_bank"
          ? blueprintSlots.map((slot) => ({
              section_index: slot.section_index,
              question_index: slot.question_index,
              chapter: slot.chapter,
              bloom: slot.bloom,
            }))
          : blueprintSlots,
    });
  }

  const steps = [
    { number: 1, title: "Configuration", description: "Scope and objectives", icon: Settings2 },
    { number: 2, title: "Template", description: "Question types and marks", icon: LayoutTemplate },
    { number: 3, title: "Blueprint", description: "Question-level allocation", icon: Network },
  ];

  return (
    <section className={`card ${styles.studio}`} aria-labelledby="question-paper-studio-title">
      <div className={styles.stepHeader} aria-label="Question paper generation steps">
        {steps.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.number}
              type="button"
              className={`${styles.stepButton} ${step === item.number ? styles.stepButtonActive : ""}`}
              onClick={() => {
                if (item.number === 1 || item.number < step) setStep(item.number);
                else if (item.number === 2) continueToTemplate();
                else continueToBlueprint();
              }}
              aria-current={step === item.number ? "step" : undefined}
            >
              <span className={styles.stepNumber}><Icon size={15} aria-hidden="true" /></span>
              <span>
                <span className={styles.stepTitle}>{item.title}</span>
                <span className={styles.stepDescription}>{item.description}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className={styles.body}>
        {step === 1 && (
          <>
            <div className={styles.intro}>
              <div>
                <h2 id="question-paper-studio-title">Configure the assessment</h2>
                <p>Set the curriculum scope and learning-objective balance before AI writes any question.</p>
              </div>
              <BookOpen size={24} color="var(--primary)" aria-hidden="true" />
            </div>

            <div className={styles.grid4}>
              <div className={styles.field}>
                <label className="stat-label" htmlFor="paper-exam-name">Paper title</label>
                <input
                  id="paper-exam-name"
                  className="form-input"
                  value={examName}
                  onChange={(event) => setExamName(event.target.value.slice(0, 200))}
                  maxLength={200}
                  style={fieldStyle}
                />
              </div>
              <div className={styles.field}>
                <label className="stat-label">Assessment type</label>
                <AppSelect
                  variant="field"
                  value={examType}
                  onChange={(value) => setExamType(value as ExamType)}
                  aria-label="Assessment type"
                  options={EXAM_TYPE_OPTIONS}
                />
              </div>
              <div className={styles.field}>
                <label className="stat-label">Class</label>
                <AppSelect
                  variant="field"
                  value={classId}
                  onChange={onClassChange}
                  aria-label="Class"
                  options={classes.map((item) => ({
                    value: item.id,
                    label: formatClassLabel(item.grade, item.section),
                  }))}
                />
              </div>
              <div className={styles.field}>
                <label className="stat-label">Subject</label>
                <AppSelect
                  variant="field"
                  value={subjectId}
                  onChange={onSubjectChange}
                  aria-label="Subject"
                  placeholder={subjects.length === 0 ? "No subjects for this class" : "Select subject"}
                  options={subjects.map((item) => ({ value: item.id, label: item.name }))}
                />
              </div>
            </div>

            <div className={`${styles.grid4} ${styles.sectionBlock}`}>
              <div className={styles.field}>
                <label className="stat-label">Generation mode</label>
                <AppSelect
                  variant="field"
                  value={generateMode}
                  onChange={(value) => changeGenerateMode(value as "full" | "from_bank")}
                  aria-label="Generation mode"
                  options={[
                    { value: "full", label: `Full AI (${fullCost} credits)` },
                    { value: "from_bank", label: `From question bank (${bankCost} credits)` },
                  ]}
                />
                {generateMode === "from_bank" && bankCount !== null && (
                  <p className={styles.fieldHint}>
                    {bankCount} approved questions in the private bank. Studio reuses exact
                    matches only and stops rather than generating ungrounded gap questions.
                  </p>
                )}
              </div>
              <div className={styles.field}>
                <label className="stat-label" htmlFor="paper-total-marks">Total marks</label>
                  <input
                    id="paper-total-marks"
                    type="number"
                    min={1}
                    max={200}
                  className="form-input"
                  value={totalMarks}
                  onChange={(event) => changeTotalMarks(Number(event.target.value))}
                  style={fieldStyle}
                />
              </div>
              <div className={styles.field}>
                <label className="stat-label" htmlFor="paper-duration">Duration (minutes)</label>
                <input
                  id="paper-duration"
                  type="number"
                  min={15}
                  max={360}
                  className="form-input"
                  value={duration}
                  onChange={(event) => setDuration(Number(event.target.value))}
                  style={fieldStyle}
                />
              </div>
              <div className={styles.field}>
                <label className="stat-label">Difficulty</label>
                <AppSelect
                  variant="field"
                  value={difficulty}
                  onChange={setDifficulty}
                  aria-label="Difficulty"
                  options={[
                    { value: "easy", label: "Easy" },
                    { value: "balanced", label: "Balanced" },
                    { value: "hard", label: "Hard" },
                  ]}
                />
              </div>
            </div>

            {generateMode === "full" && (
              <div className={styles.sectionBlock}>
                <div className={styles.grid2}>
                  <div className={styles.field}>
                    <label className="stat-label">Curriculum source</label>
                    <AppSelect
                      variant="field"
                      value={useGrounding ? "grounded" : "free"}
                      onChange={(value) => changeGrounding(value === "grounded")}
                      aria-label="Curriculum source"
                      options={[
                        { value: "grounded", label: "Approved curriculum pack" },
                        ...(canGenerateUngrounded
                          ? [{ value: "free", label: "Manual-review exception (ungrounded)" }]
                          : []),
                      ]}
                    />
                  </div>
                  {useGrounding && (
                    <div className={styles.field}>
                      <label className="stat-label">Approved curriculum pack</label>
                      <AppSelect
                        variant="field"
                        value={packId}
                        onChange={changePack}
                        aria-label="Curriculum pack"
                        options={
                          packs.length
                            ? packs.map((item) => ({
                                value: item.id,
                                label: item.book_title ? `${item.board} — ${item.book_title}` : `${item.board} pack`,
                              }))
                            : [{ value: "", label: "No approved packs" }]
                        }
                      />
                    </div>
                  )}
                </div>
                {useGrounding && packId && <AcademicIntelligenceBanner packId={packId} />}
                {useGrounding && !packs.length && classId && subjectId && (
                  <p className={styles.notice}>
                    No approved pack is available. {canEditCurriculum ? (
                      <Link href={TEACHING.curriculumOnboarding}>Complete academic onboarding first.</Link>
                    ) : (
                      "Ask a class incharge or administrator to approve one."
                    )}
                  </p>
                )}
                {!useGrounding && generateMode === "full" && (
                  <div className={styles.notice} role="alert">
                    <div className={styles.sectionHeading}>
                      <div>
                        <strong><ShieldAlert size={16} aria-hidden="true" /> Ungrounded exception</strong>
                        <p className={styles.fieldHint}>
                          This draft is outside the approved CurriculumPack path. It remains
                          non-authoritative and must be submitted for explicit approval before use.
                        </p>
                      </div>
                    </div>
                    <label className={styles.checkRow}>
                      <input
                        type="checkbox"
                        checked={ungroundedAcknowledged}
                        onChange={(event) => setUngroundedAcknowledged(event.target.checked)}
                      />
                      <span>I acknowledge that every question needs manual curriculum review.</span>
                    </label>
                    <div className={styles.field}>
                      <label className="stat-label" htmlFor="paper-ungrounded-reason">
                        Exception reason
                      </label>
                      <textarea
                        id="paper-ungrounded-reason"
                        className="form-input"
                        value={ungroundedReason}
                        onChange={(event) => setUngroundedReason(event.target.value.slice(0, 500))}
                        maxLength={500}
                        rows={2}
                        placeholder="Why can an approved curriculum pack not be used for this draft?"
                        style={fieldStyle}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className={styles.sectionBlock}>
              <div className={styles.sectionHeading}>
                <h3>Question paper scope</h3>
                {useGrounding && generateMode === "full" && (
                  <AppSelect
                    variant="field"
                    value={scopeMode}
                    onChange={(value) => selectScopeMode(value as "multiple" | "single")}
                    aria-label="Question paper scope"
                    options={[
                      { value: "multiple", label: "Multiple chapters" },
                      { value: "single", label: "Single chapter" },
                    ]}
                  />
                )}
              </div>
              {useGrounding && generateMode === "full" ? (
                packLoading ? (
                  <div className={styles.empty}>Loading approved curriculum chapters…</div>
                ) : packLoadFailed ? (
                  <div className={styles.empty} role="alert">
                    The approved curriculum pack could not be loaded. Re-select the pack or try again.
                  </div>
                ) : packDetail?.chapters.length ? (
                  <>
                    {scopeMode === "multiple" && (
                      <button
                        type="button"
                        className="btn btn-ghost"
                        style={smallButtonStyle}
                        onClick={() => {
                          const all = packDetail.chapters.map((chapter) => chapter.id);
                          updateSelectedChapters(selectedChapters.length === all.length ? [] : all);
                        }}
                      >
                        {selectedChapters.length === packDetail.chapters.length ? "Clear all" : "Select all"}
                      </button>
                    )}
                    <div className={styles.chapterPicker}>
                      {packDetail.chapters.map((chapter) => {
                        const label = chapterLabel(chapter);
                        const checked = selectedChapters.includes(chapter.id);
                        return (
                          <label key={chapter.id} className={styles.checkRow}>
                            <input
                              type={scopeMode === "single" ? "radio" : "checkbox"}
                              name="paper-chapter"
                              checked={checked}
                              onChange={() => {
                                if (scopeMode === "single") updateSelectedChapters([chapter.id]);
                                else if (checked) updateSelectedChapters(selectedChapters.filter((item) => item !== chapter.id));
                                else updateSelectedChapters([...selectedChapters, chapter.id]);
                              }}
                            />
                            <span>{label}</span>
                          </label>
                        );
                      })}
                    </div>
                  </>
                ) : (
                  <div className={styles.empty}>This approved pack has no chapters to select.</div>
                )
              ) : (
                <div className={styles.field}>
                  <label className="stat-label" htmlFor="paper-topics">Topics / chapters</label>
                  <textarea
                    id="paper-topics"
                    className="form-input"
                    value={topics}
                    onChange={(event) => changeTopics(event.target.value.slice(0, AI_INPUT.topicsRawMaxLength))}
                    maxLength={AI_INPUT.topicsRawMaxLength}
                    rows={3}
                    placeholder="Motion, Measurement, Light"
                    style={{ ...fieldStyle, resize: "vertical", fontFamily: "inherit" }}
                  />
                  <p className={styles.fieldHint}>One topic per line or comma-separated.</p>
                </div>
              )}
            </div>

            <div className={styles.sectionBlock}>
              <div className={styles.sectionHeading}>
                <h3>Learning-objective distribution</h3>
                <strong>{bloomTotal}% / 100%</strong>
              </div>
              <div className={styles.grid4}>
                {BLOOM_OPTIONS.map((option) => (
                  <div key={option.value} className={styles.field}>
                    <label className="stat-label" htmlFor={`bloom-${option.value}`}>{option.label}</label>
                    <input
                      id={`bloom-${option.value}`}
                      type="number"
                      min={0}
                      max={100}
                      className="form-input"
                      value={bloomWeights[option.value] ?? 0}
                      onChange={(event) =>
                        setBloomWeights((current) => ({ ...current, [option.value]: Number(event.target.value) }))
                      }
                      style={fieldStyle}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.sectionBlock}>
              <div className={styles.sectionHeading}>
                <h3>Marks across chapters</h3>
                <strong>{chapterTotal} / {totalMarks} marks</strong>
              </div>
              {scopeLabels.length ? (
                <div className={styles.tableWrap}>
                  <table className={styles.allocationTable}>
                    <thead><tr><th>Chapter / topic</th><th>Marks</th><th>Share</th></tr></thead>
                    <tbody>
                      {scopeKeys.map((key) => {
                        const label = chapterLabelsById[key] ?? key;
                        const marks = chapterMarks[key] ?? 0;
                        const percentage = totalMarks ? Math.round((marks / totalMarks) * 100) : 0;
                        return (
                          <tr key={key}>
                            <td>{label}</td>
                            <td>
                              <input
                                type="number"
                                min={0}
                                max={totalMarks}
                                aria-label={`${label} marks`}
                                className={styles.compactInput}
                                value={marks}
                                onChange={(event) =>
                                  setChapterMarks((current) => ({ ...current, [key]: Number(event.target.value) }))
                                }
                              />
                            </td>
                            <td style={{ minWidth: 150 }}>
                              {percentage}%
                              <div className={styles.allocationBar} aria-hidden="true">
                                <div className={styles.allocationFill} style={{ width: `${Math.max(0, Math.min(100, percentage))}%` }} />
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className={styles.empty}>Select chapters or enter topics to allocate marks.</div>
              )}
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <div className={styles.intro}>
              <div>
                <h2>Build the exact paper template</h2>
                <p>Every row is a section. The arithmetic must equal the configured paper total before proceeding.</p>
              </div>
              <LayoutTemplate size={24} color="var(--primary)" aria-hidden="true" />
            </div>
            <div className={styles.tableWrap}>
              <table className={styles.templateTable}>
                <thead>
                  <tr><th>Section</th><th>Question type</th><th>Questions</th><th>Marks each</th><th>Section marks</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {sectionPlan.map((item, index) => (
                    <tr key={`${index}-${item.title}`}>
                      <td>
                        <input
                          className={`${styles.compactInput} ${styles.titleInput}`}
                          value={item.title}
                          aria-label={`Section ${index + 1} title`}
                          onChange={(event) => updatePlan(index, { title: event.target.value.slice(0, 120) })}
                        />
                      </td>
                      <td>
                        <select
                          className={`${styles.compactInput} ${styles.titleInput}`}
                          value={item.type}
                          aria-label={`Section ${index + 1} question type`}
                          onChange={(event) => updatePlan(index, { type: event.target.value as SectionPlanItem["type"] })}
                        >
                          {QUESTION_TYPE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                        </select>
                      </td>
                      <td>
                        <input
                          type="number"
                          min={1}
                          max={60}
                          className={styles.compactInput}
                          value={item.question_count}
                          aria-label={`Section ${index + 1} question count`}
                          onChange={(event) => updatePlan(index, { question_count: Number(event.target.value) })}
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          min={1}
                          max={100}
                          className={styles.compactInput}
                          value={item.marks_per_question}
                          aria-label={`Section ${index + 1} marks per question`}
                          onChange={(event) => updatePlan(index, { marks_per_question: Number(event.target.value) })}
                        />
                      </td>
                      <td><strong>{item.question_count * item.marks_per_question}</strong></td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-ghost"
                          aria-label={`Delete ${item.title}`}
                          disabled={sectionPlan.length === 1}
                          onClick={() => setSectionPlan((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                          style={smallButtonStyle}
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              type="button"
              className="btn btn-outline"
              style={{ ...smallButtonStyle, marginTop: 14 }}
              disabled={sectionPlan.length >= 12}
              onClick={() =>
                setSectionPlan((current) => [
                  ...current,
                  {
                    title: `Section ${String.fromCharCode(65 + current.length)}`,
                    type: "short",
                    question_count: 1,
                    marks_per_question: 2,
                    instructions: "Answer all questions.",
                  },
                ])
              }
            >
              <Plus size={15} /> Add question type
            </button>
            <div className={styles.summaryStrip}>
              <div><span className={styles.summaryValue}>{sectionPlan.length}</span><span className={styles.summaryLabel}>Sections</span></div>
              <div><span className={styles.summaryValue}>{questionCount}</span><span className={styles.summaryLabel}>Questions</span></div>
              <div><span className={styles.summaryValue}>{templateTotal}</span><span className={styles.summaryLabel}>Template marks</span></div>
              <div><span className={styles.summaryValue}>{totalMarks}</span><span className={styles.summaryLabel}>Paper total</span></div>
            </div>
            {templateTotal !== totalMarks && (
              <div className={styles.warning}>Adjust the rows by {Math.abs(totalMarks - templateTotal)} marks before continuing.</div>
            )}
          </>
        )}

        {step === 3 && (
          <>
            <div className={styles.intro}>
              <div>
                <h2>Review the question-level blueprint</h2>
                <p>The allocation is deterministic. Change any chapter or objective before AI drafts the questions.</p>
              </div>
              <Network size={24} color="var(--primary)" aria-hidden="true" />
            </div>
            <div className={styles.notice}>
              StudyNexs has produced the closest valid allocation for indivisible question marks. The final paper is still a draft and requires teacher review and approval.
            </div>
            <div className={styles.summaryStrip}>
              <div><span className={styles.summaryValue}>{questionCount}</span><span className={styles.summaryLabel}>Questions</span></div>
              <div><span className={styles.summaryValue}>{totalMarks}</span><span className={styles.summaryLabel}>Marks</span></div>
              <div><span className={styles.summaryValue}>{scopeLabels.length}</span><span className={styles.summaryLabel}>Chapters / topics</span></div>
              <div><span className={styles.summaryValue}>{sectionPlan.length}</span><span className={styles.summaryLabel}>Sections</span></div>
            </div>
            <div className={`${styles.tableWrap} ${styles.scrollArea}`}>
              <table className={styles.blueprintTable}>
                <thead><tr><th>Question</th><th>Type</th><th>Marks</th><th>Chapter / topic</th><th>Learning objective</th></tr></thead>
                <tbody>
                  {blueprintSlots.map((slot, slotIndex) => {
                    const section = sectionPlan[slot.section_index];
                    return (
                      <tr key={`${slot.section_index}-${slot.question_index}`}>
                        <td><strong>{section?.title} · Q{slot.question_index + 1}</strong></td>
                        <td>{QUESTION_TYPE_OPTIONS.find((option) => option.value === section?.type)?.label ?? section?.type}</td>
                        <td>{section?.marks_per_question}</td>
                        <td>
                          <select
                            className={`${styles.compactInput} ${styles.titleInput}`}
                            value={groundedScope ? (slot.chapter_id ?? "") : slot.chapter}
                            aria-label={`Question ${slotIndex + 1} chapter`}
                            onChange={(event) => {
                              const selectedKey = event.target.value;
                              setBlueprintSlots((current) => current.map((item, index) => (
                                index === slotIndex
                                  ? {
                                      ...item,
                                      chapter_id: groundedScope ? selectedKey : undefined,
                                      chapter: chapterLabelsById[selectedKey] ?? selectedKey,
                                    }
                                  : item
                              )));
                            }}
                          >
                            {scopeKeys.map((key) => (
                              <option key={key} value={key}>{chapterLabelsById[key] ?? key}</option>
                            ))}
                          </select>
                        </td>
                        <td>
                          <select
                            className={`${styles.compactInput} ${styles.titleInput}`}
                            value={slot.bloom}
                            aria-label={`Question ${slotIndex + 1} objective`}
                            onChange={(event) =>
                              setBlueprintSlots((current) => current.map((item, index) => index === slotIndex ? { ...item, bloom: event.target.value as BlueprintSlot["bloom"] } : item))
                            }
                          >
                            {BLOOM_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {(localError || error) && <div className={styles.error} role="alert">{localError || error}</div>}
        {generating && (
          <div className={styles.notice} role="status">
            Drafting the paper inside the approved blueprint. This usually takes 15–30 seconds…
          </div>
        )}

        <div className={styles.footer}>
          <span className={styles.fieldHint}>AI drafts; the teacher reviews, edits, and approves.</span>
          <div className={styles.footerActions}>
            {step > 1 && (
              <button type="button" className="btn btn-outline" style={smallButtonStyle} onClick={() => setStep((current) => current - 1)}>
                <ChevronLeft size={15} /> Previous
              </button>
            )}
            {step === 1 && (
              <button type="button" className="btn btn-primary" style={primaryButtonStyle} onClick={continueToTemplate}>
                Continue to template <ChevronRight size={15} />
              </button>
            )}
            {step === 2 && (
              <button type="button" className="btn btn-primary" style={primaryButtonStyle} onClick={continueToBlueprint}>
                Build blueprint <ChevronRight size={15} />
              </button>
            )}
            {step === 3 && (
              <button type="button" className="btn btn-primary" style={primaryButtonStyle} disabled={generating} onClick={submitGeneration}>
                <Sparkles size={16} /> {generating ? "Generating…" : "Generate question paper"}
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

const fieldStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--border)",
  background: "white",
  marginTop: 4,
};

const smallButtonStyle: React.CSSProperties = {
  width: "auto",
  padding: "8px 14px",
  borderRadius: "var(--radius-full)",
  fontSize: 13,
};

const primaryButtonStyle: React.CSSProperties = {
  ...smallButtonStyle,
  padding: "9px 18px",
};
