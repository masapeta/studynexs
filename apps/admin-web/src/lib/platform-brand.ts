/** Shared platform brand constants — safe for server and client imports. */

export type PlatformMarkVariant = "studynexs" | "noustriks";

export const PLATFORM_MARKS: Record<PlatformMarkVariant, string> = {
  studynexs: "S",
  noustriks: "N",
};

export const PLATFORM_PRODUCT_NAME = "StudyNexs";

export const DEFAULT_ENTRY_MESSAGE = "Opening your school workspace…";

export type PortalEntryContext =
  | "default"
  | "teacher"
  | "parent"
  | "student"
  | "admin";

const ENTRY_MESSAGES: Record<PortalEntryContext, string> = {
  default: DEFAULT_ENTRY_MESSAGE,
  admin: DEFAULT_ENTRY_MESSAGE,
  teacher: "Opening your teacher workspace…",
  parent: "Opening your parent portal…",
  student: "Opening your student workspace…",
};

export function entryMessageForPortal(context: PortalEntryContext): string {
  return ENTRY_MESSAGES[context];
}
