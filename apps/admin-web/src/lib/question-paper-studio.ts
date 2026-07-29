export type BloomLevel = "remember" | "understand" | "apply" | "analyse";

export type { ExamType } from "./exam-types";
export { EXAM_TYPE_OPTIONS } from "./exam-types";

export type SectionPlanItem = {
  title: string;
  type: "mcq" | "fill_blank" | "match" | "very_short" | "short" | "long";
  question_count: number;
  marks_per_question: number;
  instructions?: string;
};

export type BlueprintSlot = {
  section_index: number;
  question_index: number;
  chapter_id?: string;
  chapter: string;
  bloom: BloomLevel;
};

export type Allocation = Record<string, number>;

export const BLOOM_OPTIONS: { value: BloomLevel; label: string }[] = [
  { value: "remember", label: "Knowledge" },
  { value: "understand", label: "Understanding" },
  { value: "apply", label: "Application" },
  { value: "analyse", label: "Higher-order thinking" },
];

export const QUESTION_TYPE_OPTIONS = [
  { value: "mcq", label: "Objective questions (MCQ)" },
  { value: "fill_blank", label: "Fill in the blanks" },
  { value: "match", label: "Match the following" },
  { value: "very_short", label: "Very short answer" },
  { value: "short", label: "Short answer" },
  { value: "long", label: "Long answer" },
] as const;

const QUESTION_OUTPUT_TOKEN_BUDGET = 6_000;
const QUESTION_OUTPUT_TOKEN_WEIGHTS: Record<SectionPlanItem["type"], number> = {
  mcq: 90,
  fill_blank: 60,
  match: 120,
  very_short: 70,
  short: 120,
  long: 220,
};

export function sumSectionPlan(plan: SectionPlanItem[]): number {
  return plan.reduce(
    (total, item) => total + item.question_count * item.marks_per_question,
    0
  );
}

export function buildDefaultSectionPlan(totalMarks: number): SectionPlanItem[] {
  const bounded = Math.max(1, Math.min(200, Math.trunc(totalMarks || 1)));
  if (bounded <= 10) {
    return [
      {
        title: "Section A",
        type: "mcq",
        question_count: bounded,
        marks_per_question: 1,
        instructions: "Answer all questions.",
      },
    ];
  }

  let objectiveCount = Math.max(4, Math.round(bounded * 0.25));
  let longCount = Math.floor((bounded * 0.25) / 5);
  let remainder = bounded - objectiveCount - longCount * 5;
  let shortCount = Math.floor(remainder / 2);
  if (remainder % 2 !== 0) objectiveCount += 1;
  remainder = bounded - objectiveCount - longCount * 5 - shortCount * 2;

  if (remainder < 0) {
    longCount = Math.max(0, longCount - 1);
    shortCount = Math.floor((bounded - objectiveCount - longCount * 5) / 2);
  }
  const used = objectiveCount + shortCount * 2 + longCount * 5;
  objectiveCount += bounded - used;

  const plan: SectionPlanItem[] = [
    {
      title: "Section A",
      type: "mcq",
      question_count: objectiveCount,
      marks_per_question: 1,
      instructions: "Choose the correct answer.",
    },
  ];
  if (shortCount > 0) {
    plan.push({
      title: "Section B",
      type: "short",
      question_count: shortCount,
      marks_per_question: 2,
      instructions: "Answer all questions briefly.",
    });
  }
  if (longCount > 0) {
    plan.push({
      title: `Section ${String.fromCharCode(65 + plan.length)}`,
      type: "long",
      question_count: longCount,
      marks_per_question: 5,
      instructions: "Answer all questions in detail.",
    });
  }
  return plan;
}

export function distributeTotal(keys: string[], total: number): Allocation {
  if (keys.length === 0) return {};
  const safeTotal = Math.max(0, Math.trunc(total));
  const base = Math.floor(safeTotal / keys.length);
  let remainder = safeTotal - base * keys.length;
  return Object.fromEntries(
    keys.map((key) => {
      const value = base + (remainder > 0 ? 1 : 0);
      if (remainder > 0) remainder -= 1;
      return [key, value];
    })
  );
}

export function distributeByWeight(weights: Allocation, total: number): Allocation {
  const entries = Object.entries(weights);
  if (entries.length === 0) return {};
  const weightTotal = entries.reduce((sum, [, value]) => sum + Math.max(0, value), 0);
  if (weightTotal <= 0) return distributeTotal(entries.map(([key]) => key), total);

  const raw = entries.map(([key, weight], index) => {
    const exact = (Math.max(0, weight) / weightTotal) * total;
    return { key, index, floor: Math.floor(exact), fraction: exact - Math.floor(exact) };
  });
  let remainder = total - raw.reduce((sum, item) => sum + item.floor, 0);
  const ranked = [...raw].sort(
    (left, right) => right.fraction - left.fraction || left.index - right.index
  );
  for (const item of ranked) {
    if (remainder <= 0) break;
    item.floor += 1;
    remainder -= 1;
  }
  return Object.fromEntries(raw.map((item) => [item.key, item.floor]));
}

function chooseTarget(remaining: Allocation, order: string[]): string {
  let selected = order[0] || "";
  for (const key of order) {
    if ((remaining[key] ?? 0) > (remaining[selected] ?? Number.NEGATIVE_INFINITY)) {
      selected = key;
    }
  }
  return selected;
}

export function buildBlueprintSlots(
  plan: SectionPlanItem[],
  chapterTargets: Allocation,
  bloomTargets: Allocation
): BlueprintSlot[] {
  const chapters = Object.keys(chapterTargets);
  const blooms = BLOOM_OPTIONS.map((option) => option.value);
  if (chapters.length === 0) return [];

  const chapterRemaining = { ...chapterTargets };
  const bloomRemaining = { ...bloomTargets };
  const slots: BlueprintSlot[] = [];

  plan.forEach((section, sectionIndex) => {
    for (let questionIndex = 0; questionIndex < section.question_count; questionIndex += 1) {
      const chapter = chooseTarget(chapterRemaining, chapters);
      const bloom = chooseTarget(bloomRemaining, blooms) as BloomLevel;
      slots.push({ section_index: sectionIndex, question_index: questionIndex, chapter, bloom });
      chapterRemaining[chapter] = (chapterRemaining[chapter] ?? 0) - section.marks_per_question;
      bloomRemaining[bloom] = (bloomRemaining[bloom] ?? 0) - section.marks_per_question;
    }
  });
  return slots;
}

export function validateSectionPlan(plan: SectionPlanItem[], totalMarks: number): string | null {
  if (plan.length === 0) return "Add at least one question type.";
  if (plan.length > 12) return "Use no more than 12 sections.";
  const questionCount = plan.reduce((sum, item) => sum + item.question_count, 0);
  if (questionCount > 120) return "Use no more than 120 questions in one paper.";
  for (const item of plan) {
    if (!item.title.trim()) return "Every section needs a title.";
    if (!Number.isInteger(item.question_count) || item.question_count < 1 || item.question_count > 60) {
      return "Question counts must be whole numbers from 1 to 60.";
    }
    if (!Number.isInteger(item.marks_per_question) || item.marks_per_question < 1 || item.marks_per_question > 100) {
      return "Marks per question must be whole numbers from 1 to 100.";
    }
  }
  const titles = plan.map((item) => item.title.trim().toLowerCase());
  if (new Set(titles).size !== titles.length) return "Section titles must be unique.";
  const estimatedOutput = plan.reduce(
    (sum, item) => sum + item.question_count * QUESTION_OUTPUT_TOKEN_WEIGHTS[item.type],
    0
  );
  if (estimatedOutput > QUESTION_OUTPUT_TOKEN_BUDGET) {
    return "This template is too large for one reliable generation. Reduce the question count or use fewer long-answer questions.";
  }
  const planTotal = sumSectionPlan(plan);
  if (planTotal !== totalMarks) {
    return `Template total is ${planTotal}; it must equal ${totalMarks} marks.`;
  }
  return null;
}
