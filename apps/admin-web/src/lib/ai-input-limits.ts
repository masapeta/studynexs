/** Shared client-side limits for AI features — mirrors API input_guard bounds. */

export const AI_INPUT = {
  topicMaxCount: 20,
  topicMaxLength: 120,
  topicsRawMaxLength: 2000,
  paperTitleMaxLength: 200,
  reportTitleMaxLength: 200,
  reportRemarkMaxLength: 4000,
  masteryNarrativeMaxLength: 2000,
  answerMaxLength: 2000,
  answerMaxKeys: 100,
  answerSheetMaxBytes: 5 * 1024 * 1024,
  answerSheetMimeTypes: ["image/jpeg", "image/png", "image/webp"] as const,
  ttsMaxLength: 1200,
  rejectReasonMaxLength: 500,
  dismissReasonMaxLength: 300,
} as const;

const INJECTION_RE =
  /ignore\s+(all\s+)?(previous|prior|above)\s+instructions|forget\s+(all\s+)?(previous|prior|your)\s+instructions|disregard\s+(all\s+)?(previous|prior|above)\s+instructions|you\s+are\s+now|new\s+instructions?\s*:|override\s+(system|safety|content)\s+(prompt|rules|policy)|<\s*\/?\s*system\s*>|```\s*system|\[INST\]|<\|im_start\|>|<\|im_end\|>|<<SYS>>/i;

export function assertNoPromptInjection(value: string, fieldLabel = "Text"): void {
  if (INJECTION_RE.test(value)) {
    throw new Error(`${fieldLabel} contains disallowed content`);
  }
}

export function parseTopicList(raw: string): string[] {
  const trimmed = raw.trim().slice(0, AI_INPUT.topicsRawMaxLength);
  const parts = trimmed
    .split(/[\n,]/)
    .map((t) => t.trim())
    .filter(Boolean);
  if (parts.length > AI_INPUT.topicMaxCount) {
    throw new Error(`At most ${AI_INPUT.topicMaxCount} topics allowed`);
  }
  for (const p of parts) {
    if (p.length > AI_INPUT.topicMaxLength) {
      throw new Error(`Each topic must be at most ${AI_INPUT.topicMaxLength} characters`);
    }
    assertNoPromptInjection(p, "Topics");
  }
  return parts;
}

export function validateAnswerSheetFile(file: File): string | null {
  if (file.size > AI_INPUT.answerSheetMaxBytes) {
    return "Answer sheet image must be 5 MB or smaller";
  }
  if (!AI_INPUT.answerSheetMimeTypes.includes(file.type as (typeof AI_INPUT.answerSheetMimeTypes)[number])) {
    return "Use a JPEG, PNG, or WebP image for answer sheets";
  }
  return null;
}

export function clampText(value: string, max: number): string {
  return value.slice(0, max);
}

/** Clamp and reject prompt-injection phrases on teacher-edited AI text fields. */
export function sanitizeAiText(value: string, max: number, fieldLabel = "Text"): string {
  const trimmed = value.slice(0, max);
  assertNoPromptInjection(trimmed, fieldLabel);
  return trimmed;
}
