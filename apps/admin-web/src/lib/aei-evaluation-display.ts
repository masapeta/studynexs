export type AeiSuggestionLike = {
  confidence?: unknown;
  method?: unknown;
  manual_review_required?: unknown;
  manual_review_reason?: unknown;
  confidence_reason?: unknown;
  capability_mode?: unknown;
  normalized_answer?: unknown;
  matched_acceptable_answer?: unknown;
  interpreted_value?: unknown;
  matched_value?: unknown;
  unit_result?: unknown;
  tolerance_result?: unknown;
  answer_language?: unknown;
  detected_script?: unknown;
  code_mixed?: unknown;
  language_confidence?: unknown;
  ocr_confidence?: unknown;
  answer_input_source?: unknown;
  language_ocr_capability_mode?: unknown;
  visual_science_capability_mode?: unknown;
  visual_science_review_required?: unknown;
  visual_science_reasoning_type?: unknown;
  visual_type?: unknown;
  scientific_type?: unknown;
  assist_only?: unknown;
  checklist_only?: unknown;
  aei_v1?: unknown;
  aei_v1_review_policy?: unknown;
  aei_v1_language_ocr_assist?: unknown;
  aei_v1_visual_science_assist?: unknown;
};

export type AeiBadgeTone = "neutral" | "success" | "warning" | "danger";

export type AeiTrustBadge = {
  label: string;
  tone: AeiBadgeTone;
  title?: string;
};

export type AeiEvidenceRow = {
  label: string;
  value: string;
};

export type AeiAssistEvidencePanel = {
  title: string;
  posture: string;
  boundaryCopy: string;
  tone: AeiBadgeTone;
  rows: AeiEvidenceRow[];
  observations: AeiEvidenceRow[];
};

export type AeiEvaluationTrustSummary = {
  totalQuestions: number;
  questionsWithAeiMetadata: number;
  questionsWithConfidence: number;
  manualReviewRequired: number;
  lowConfidence: number;
  assistOrChecklist: number;
  deterministicSupported: number;
};

const LOW_CONFIDENCE_THRESHOLD = 0.75;
const HIGH_CONFIDENCE_THRESHOLD = 0.85;
const REVIEW_MODES = new Set([
  "assist",
  "checklist",
  "manual_review",
  "partial",
  "unsupported",
  "expansion",
]);

export function buildAeiEvaluationTrustSummary(
  suggestions: Record<string, unknown> | null | undefined,
): AeiEvaluationTrustSummary {
  const values = suggestionValues(suggestions);
  return values.reduce<AeiEvaluationTrustSummary>(
    (summary, suggestion) => {
      const confidence = numberValue(suggestion.confidence);
      const mode = stringValue(suggestion.capability_mode);

      summary.totalQuestions += 1;
      if (hasAeiMetadata(suggestion)) summary.questionsWithAeiMetadata += 1;
      if (confidence !== null) summary.questionsWithConfidence += 1;
      if (suggestion.manual_review_required === true) summary.manualReviewRequired += 1;
      if (confidence !== null && confidence < LOW_CONFIDENCE_THRESHOLD) {
        summary.lowConfidence += 1;
      }
      if (
        REVIEW_MODES.has(normalizeMode(mode)) ||
        suggestion.assist_only === true ||
        suggestion.checklist_only === true
      ) {
        summary.assistOrChecklist += 1;
      }
      if (normalizeMode(mode) === "supported" && hasAeiMetadata(suggestion)) {
        summary.deterministicSupported += 1;
      }
      return summary;
    },
    {
      totalQuestions: 0,
      questionsWithAeiMetadata: 0,
      questionsWithConfidence: 0,
      manualReviewRequired: 0,
      lowConfidence: 0,
      assistOrChecklist: 0,
      deterministicSupported: 0,
    },
  );
}

export function buildAeiSuggestionTrustBadges(
  suggestion: AeiSuggestionLike,
): AeiTrustBadge[] {
  const badges: AeiTrustBadge[] = [];
  const confidence = numberValue(suggestion.confidence);
  const mode = stringValue(suggestion.capability_mode);
  const manualReason = stringValue(suggestion.manual_review_reason);

  if (confidence !== null) {
    badges.push({
      label: `Confidence ${Math.round(confidence * 100)}%`,
      tone:
        confidence < LOW_CONFIDENCE_THRESHOLD
          ? "warning"
          : confidence >= HIGH_CONFIDENCE_THRESHOLD
            ? "success"
            : "neutral",
      title: stringValue(suggestion.confidence_reason) || undefined,
    });
  }

  const capability = capabilityBadge(mode);
  if (capability) badges.push(capability);

  const method = methodBadge(stringValue(suggestion.method));
  if (method) badges.push(method);

  if (suggestion.manual_review_required === true) {
    badges.push({
      label: "Teacher review required",
      tone: "warning",
      title: manualReason || undefined,
    });
  }

  if (stringValue(suggestion.normalized_answer) || stringValue(suggestion.matched_acceptable_answer)) {
    badges.push({ label: "Maths equivalence", tone: "success" });
  }

  const language = stringValue(suggestion.answer_language);
  const script = stringValue(suggestion.detected_script);
  if (language || script || suggestion.code_mixed === true) {
    badges.push({
      label: languageAndScriptLabel(language, script, suggestion.code_mixed === true),
      tone: suggestion.manual_review_required === true ? "warning" : "neutral",
    });
  }

  const ocrConfidence = numberValue(suggestion.ocr_confidence);
  if (ocrConfidence !== null) {
    badges.push({
      label: `OCR ${Math.round(ocrConfidence * 100)}%`,
      tone: ocrConfidence < LOW_CONFIDENCE_THRESHOLD ? "warning" : "neutral",
    });
  }

  if (suggestion.checklist_only === true) {
    badges.push({ label: "Checklist only", tone: "warning" });
  } else if (suggestion.assist_only === true) {
    badges.push({ label: "Assist only", tone: "warning" });
  }

  const visualMode = stringValue(suggestion.visual_science_capability_mode);
  if (visualMode && visualMode !== mode) {
    const visual = capabilityBadge(visualMode);
    if (visual) {
      badges.push({ ...visual, label: `Visual/science: ${visual.label}` });
    }
  }

  return uniqueBadges(badges);
}

export function buildAeiEvidenceRows(suggestion: AeiSuggestionLike): AeiEvidenceRow[] {
  const rows: AeiEvidenceRow[] = [];
  addEvidence(rows, "Normalized answer", suggestion.normalized_answer);
  addEvidence(rows, "Matched acceptable answer", suggestion.matched_acceptable_answer);
  addEvidence(rows, "Interpreted value", suggestion.interpreted_value);
  addEvidence(rows, "Matched value", suggestion.matched_value);
  addEvidence(rows, "Unit result", suggestion.unit_result);
  addEvidence(rows, "Tolerance result", suggestion.tolerance_result);
  addEvidence(rows, "Manual review reason", suggestion.manual_review_reason);
  return rows;
}

export function buildAeiAssistEvidencePanels(
  suggestion: AeiSuggestionLike,
): AeiAssistEvidencePanel[] {
  return [
    buildLanguageOcrAssistPanel(suggestion),
    buildVisualScienceAssistPanel(suggestion),
  ].filter((panel): panel is AeiAssistEvidencePanel => panel !== null);
}

export function hasAeiMetadata(suggestion: AeiSuggestionLike): boolean {
  return Boolean(
    suggestion.aei_v1 ||
      suggestion.aei_v1_review_policy ||
      suggestion.aei_v1_language_ocr_assist ||
      suggestion.aei_v1_visual_science_assist ||
      suggestion.manual_review_required === true ||
      suggestion.capability_mode ||
      suggestion.normalized_answer ||
      suggestion.matched_acceptable_answer,
  );
}

function buildLanguageOcrAssistPanel(
  suggestion: AeiSuggestionLike,
): AeiAssistEvidencePanel | null {
  const assist = recordValue(suggestion.aei_v1_language_ocr_assist);
  const rows: AeiEvidenceRow[] = [];
  const observations: AeiEvidenceRow[] = [];
  const answerSource = firstDisplayValue(suggestion.answer_input_source, assist?.answer_input_source);
  const language = firstDisplayValue(suggestion.answer_language, assist?.detected_language);
  const script = firstDisplayValue(suggestion.detected_script, assist?.detected_script);
  const capability = firstDisplayValue(
    suggestion.language_ocr_capability_mode,
    assist?.capability_mode,
  );
  const languageConfidence = firstConfidenceValue(
    suggestion.language_confidence,
    assist?.language_confidence,
  );
  const ocrConfidence = firstConfidenceValue(suggestion.ocr_confidence, assist?.ocr_confidence);
  const reviewReason = firstReviewReason(suggestion.manual_review_reason, assist?.review_reasons);

  addEvidence(rows, "Source", answerSource);
  addEvidence(rows, "Detected language", language);
  addEvidence(rows, "Detected script", script);
  if (suggestion.code_mixed === true || assist?.code_mixed === true) {
    addEvidence(rows, "Code-mixed posture", "Code-mixed detected");
  }
  addEvidence(rows, "Language confidence", languageConfidence);
  addEvidence(rows, "OCR confidence", ocrConfidence);
  addEvidence(rows, "Capability posture", capability ? capabilityWording(capability) : "");
  addEvidence(rows, "Review reason", reviewReason);
  addEvidence(observations, "OCR confidence threshold", firstConfidenceValue(assist?.ocr_confidence_threshold));
  if (assist?.ocr_confidence_missing === true) {
    addEvidence(observations, "OCR confidence", "Unavailable - teacher confirmation required");
  }
  if (assist?.low_ocr_confidence === true) {
    addEvidence(observations, "OCR confidence", "Below teacher-review threshold");
  }
  if (assist?.autonomous_language_grading === false) {
    addEvidence(observations, "Language grading", "Not autonomous");
  }

  if (!assist && rows.length === 0 && observations.length === 0) return null;

  return {
    title: "Language/OCR assist",
    posture: "Assistive evidence only - teacher confirmation required",
    boundaryCopy: "OCR/language assist does not certify marks. Confirm the answer text before approving.",
    tone: "warning",
    rows,
    observations,
  };
}

function buildVisualScienceAssistPanel(
  suggestion: AeiSuggestionLike,
): AeiAssistEvidencePanel | null {
  const assist = recordValue(suggestion.aei_v1_visual_science_assist);
  const summary = recordValue(assist?.evidence_summary);
  const rows: AeiEvidenceRow[] = [];
  const observations: AeiEvidenceRow[] = [];
  const capability = firstDisplayValue(
    suggestion.visual_science_capability_mode,
    assist?.capability_mode,
  );
  const reasoningType = firstDisplayValue(
    suggestion.visual_science_reasoning_type,
    assist?.reasoning_type,
  );
  const visualType = firstDisplayValue(suggestion.visual_type, assist?.visual_type);
  const scientificType = firstDisplayValue(suggestion.scientific_type, assist?.scientific_type);
  const reviewReason = firstReviewReason(suggestion.manual_review_reason, assist?.review_reasons);

  addEvidence(rows, "Capability posture", capability ? capabilityWording(capability) : "");
  addEvidence(rows, "Reasoning type", reasoningType);
  addEvidence(rows, "Visual type", visualType);
  addEvidence(rows, "Scientific type", scientificType);
  if (suggestion.visual_science_review_required === true || assist?.manual_review_required === true) {
    addEvidence(rows, "Teacher review", "Required");
  }
  if (suggestion.checklist_only === true || assist?.checklist_only === true) {
    addEvidence(rows, "Checklist posture", "Checklist only - teacher confirmation required");
  }
  if (suggestion.assist_only === true || assist?.assist_only === true) {
    addEvidence(rows, "Assist posture", "Assist only - teacher confirmation required");
  }
  addEvidence(rows, "Review reason", reviewReason);

  addEvidence(observations, "Checklist expected", assist?.checklist_expected);
  addEvidence(observations, "Checklist observed", assist?.checklist_observed);
  addEvidence(observations, "Checklist present", summary?.checklist_present);
  addEvidence(observations, "Checklist missing", summary?.checklist_missing);
  addEvidence(observations, "Reasoning result", firstDisplayValue(assist?.reasoning_result, summary?.reasoning_result));
  addEvidence(observations, "Chemical balance status", summary?.chemical_balance_status);
  addEvidence(observations, "Chemical symbols", summary?.chemical_symbols);
  addEvidence(observations, "Formula detected", summary?.formula_detected);
  if (assist?.autonomous_marks_from_checklist === false) {
    addEvidence(observations, "Marks from checklist", "Not autonomous");
  }
  if (assist?.autonomous_visual_grading === false) {
    addEvidence(observations, "Visual grading", "Not autonomous");
  }
  if (assist?.autonomous_science_grading === false) {
    addEvidence(observations, "Science grading", "Not autonomous");
  }

  if (!assist && rows.length === 0 && observations.length === 0) return null;

  return {
    title: "Visual/science assist",
    posture: "Checklist/assist evidence only - teacher confirmation required",
    boundaryCopy: "Checklist observations support your review. They do not automatically award marks.",
    tone: "warning",
    rows,
    observations,
  };
}

function suggestionValues(
  suggestions: Record<string, unknown> | null | undefined,
): AeiSuggestionLike[] {
  return Object.values(suggestions || {}).filter(isSuggestionLike);
}

function isSuggestionLike(value: unknown): value is AeiSuggestionLike {
  return Boolean(value && typeof value === "object");
}

function addEvidence(rows: AeiEvidenceRow[], label: string, value: unknown) {
  const text = displayValue(value);
  if (text) rows.push({ label, value: text });
}

function recordValue(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function firstDisplayValue(...values: unknown[]): string {
  for (const value of values) {
    const text = displayValue(value);
    if (text) return text;
  }
  return "";
}

function firstConfidenceValue(...values: unknown[]): string {
  for (const value of values) {
    const confidence = numberValue(value);
    if (confidence !== null) return `${Math.round(confidence * 100)}%`;
  }
  return "";
}

function firstReviewReason(primary: unknown, fallback: unknown): string {
  const direct = displayValue(primary);
  if (direct) return direct;
  if (Array.isArray(fallback)) return fallback.map(displayValue).filter(Boolean).join("; ");
  return displayValue(fallback);
}

function capabilityWording(mode: string): string {
  switch (normalizeMode(mode)) {
    case "assist":
      return "Assist only - teacher confirmation required";
    case "checklist":
      return "Checklist only - teacher confirmation required";
    case "manual_review":
      return "Teacher review required";
    case "unsupported":
      return "Not supported for automatic evaluation";
    case "expansion":
      return "Future scope";
    case "supported":
      return "Supported";
    case "partial":
      return "Partial support - teacher confirmation required";
    default:
      return mode;
  }
}

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map(displayValue).filter(Boolean).join(", ");
  if (typeof value === "object") {
    try {
      return JSON.stringify(value);
    } catch {
      return "";
    }
  }
  return String(value);
}

function stringValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return clampConfidence(value);
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return clampConfidence(parsed);
  }
  return null;
}

function clampConfidence(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function normalizeMode(value: string): string {
  return value.trim().toLowerCase();
}

function capabilityBadge(mode: string): AeiTrustBadge | null {
  switch (normalizeMode(mode)) {
    case "supported":
      return { label: "Supported", tone: "success" };
    case "assist":
      return { label: "Assist only", tone: "warning" };
    case "checklist":
      return { label: "Checklist only", tone: "warning" };
    case "manual_review":
      return { label: "Manual review", tone: "warning" };
    case "partial":
      return { label: "Partial support", tone: "warning" };
    case "unsupported":
      return { label: "Unsupported", tone: "danger" };
    case "expansion":
      return { label: "Future scope", tone: "neutral" };
    default:
      return null;
  }
}

function methodBadge(method: string): AeiTrustBadge | null {
  switch (method) {
    case "aei_v1_math_normalization":
      return { label: "AEI Maths", tone: "success" };
    case "aei_v1_language_ocr_assist":
      return { label: "Language/OCR assist", tone: "warning" };
    case "aei_v1_visual_science_assist":
      return { label: "Visual/science assist", tone: "warning" };
    case "objective":
      return { label: "Objective", tone: "neutral" };
    case "llm_rubric":
      return { label: "Rubric AI", tone: "neutral" };
    case "heuristic_fallback":
      return { label: "Heuristic", tone: "warning" };
    default:
      return null;
  }
}

function languageAndScriptLabel(language: string, script: string, codeMixed: boolean): string {
  const parts = [language, script].filter(Boolean);
  if (codeMixed) parts.push("code-mixed");
  return parts.length ? parts.join(" / ") : "Language detected";
}

function uniqueBadges(badges: AeiTrustBadge[]): AeiTrustBadge[] {
  const seen = new Set<string>();
  return badges.filter((badge) => {
    const key = `${badge.label}:${badge.tone}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
