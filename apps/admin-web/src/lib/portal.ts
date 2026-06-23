/** Portal routing — where each role lands after login. */

export type PortalKind = "staff" | "teacher" | "parent" | "student";

export function portalFromRole(role: string): PortalKind {
  if (role === "parent") return "parent";
  if (role === "student") return "student";
  if (role === "teacher" || role === "class_incharge") return "teacher";
  return "staff";
}

export function homePathForRole(role: string): string {
  const portal = portalFromRole(role);
  switch (portal) {
    case "parent":
      return "/parent";
    case "student":
      return "/student";
    case "teacher":
      return "/teacher";
    default:
      return "/dashboard";
  }
}

export const DEMO_LOGINS = {
  staff: { label: "Principal", username: "principal", password: "Demo@1234" },
  teacher: { label: "Maths Teacher", username: "teacher6", password: "Demo@1234" },
  parent: { label: "Parent (demo)", username: "parent_demo", password: "Demo@1234" },
  student: { label: "Student (demo)", username: "student_demo", password: "Demo@1234" },
} as const;

export type DemoPortalKey = keyof typeof DEMO_LOGINS;

export async function homePathAfterLogin(): Promise<string> {
  const { api } = await import("@/lib/api");
  const profile = await api<{ data: { role: string } }>("/api/v1/users/me");
  return homePathForRole(profile.data.role);
}
