/** Browser speech fallback — never pick male Indian voices (Ravi, Prabhat, etc.). */

const FEMALE_HINT =
  /(heera|neerja|neerjaexpressive|aarohi|ananya|kalpana|swara|shruti|sapna|tanishaa|dhwani|asha|veena|priya|isha|zira|jenny|samantha|sara|sonia|aria|female|woman)/i;

const MALE_HINT =
  /(ravi|prabhat|madhur|hemant|valluvar|david|mark|guy|james|ryan|male|man\b)/i;

function voiceLabel(v: SpeechSynthesisVoice): string {
  return `${v.name} ${v.voiceURI} ${v.lang}`.toLowerCase();
}

export function isMaleBrowserVoice(v: SpeechSynthesisVoice): boolean {
  return MALE_HINT.test(voiceLabel(v));
}

export function isFemaleBrowserVoice(v: SpeechSynthesisVoice): boolean {
  const label = voiceLabel(v);
  return FEMALE_HINT.test(label) && !MALE_HINT.test(label);
}

/** Best-effort female teacher voice; null if none found (prefer cloud TTS instead). */
export function pickFemaleTeacherVoice(
  voices: SpeechSynthesisVoice[]
): SpeechSynthesisVoice | null {
  if (!voices.length) return null;

  const indianEn = voices.filter((v) => {
    const lang = (v.lang || "").toLowerCase();
    return lang === "en-in" || /india/i.test(v.name);
  });

  const femaleIndian = indianEn.filter((v) => isFemaleBrowserVoice(v) && !isMaleBrowserVoice(v));
  if (femaleIndian.length) return femaleIndian[0];

  const femaleEn = voices.filter(
    (v) =>
      (v.lang || "").toLowerCase().startsWith("en") &&
      isFemaleBrowserVoice(v) &&
      !isMaleBrowserVoice(v)
  );
  if (femaleEn.length) return femaleEn[0];

  const anyFemale = voices.filter((v) => isFemaleBrowserVoice(v) && !isMaleBrowserVoice(v));
  return anyFemale[0] ?? null;
}
