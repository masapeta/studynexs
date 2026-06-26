export type AdmissionCandidate = {
  id: string;
  name: string;
  grade_applied: string;
  stage: string;
  enquiry_date: string;
  date_of_birth?: string | null;
  gender?: string | null;
  parent_name?: string | null;
  parent_relation?: string | null;
  parent_occupation?: string | null;
  parent_mobile?: string | null;
  parent_email?: string | null;
  address_line?: string | null;
  city?: string | null;
  previous_school_name?: string | null;
  previous_grade?: string | null;
  enquiry_source?: string | null;
  aadhaar_number?: string | null;
  birth_certificate_number?: string | null;
  apaar_number?: string | null;
  notes?: string | null;
  stage_details?: Record<string, Record<string, unknown>>;
};

const GENDER_LABELS: Record<string, string> = {
  male: "Male",
  female: "Female",
  other: "Other",
};

const RELATION_LABELS: Record<string, string> = {
  father: "Father",
  mother: "Mother",
  guardian: "Guardian",
};

const SOURCE_LABELS: Record<string, string> = {
  walk_in: "Walk-in",
  referral: "Referral",
  website: "Website",
  phone: "Phone call",
  social: "Social media",
  other: "Other",
};

export function formatAdmissionDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  } catch {
    return iso;
  }
}

export function labelFor(
  value: string | null | undefined,
  labels: Record<string, string>
): string {
  if (!value) return "—";
  return labels[value] || value;
}

export function displayText(value: string | null | undefined): string {
  const trimmed = value?.trim();
  return trimmed || "—";
}

export function genderLabel(value: string | null | undefined) {
  return labelFor(value, GENDER_LABELS);
}

export function relationLabel(value: string | null | undefined) {
  return labelFor(value, RELATION_LABELS);
}

export function sourceLabel(value: string | null | undefined) {
  return labelFor(value, SOURCE_LABELS);
}

export function stageLabel(stage: string) {
  return stage.charAt(0).toUpperCase() + stage.slice(1);
}
