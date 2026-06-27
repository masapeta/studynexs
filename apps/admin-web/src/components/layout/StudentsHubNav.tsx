"use client";

import { ModuleHubNav } from "./ModuleHubNav";
import { STUDENTS } from "@/lib/dashboard-routes";

function isEnrolledPath(pathname: string): boolean {
  if (pathname === STUDENTS.admissions || pathname.startsWith(`${STUDENTS.admissions}/`)) {
    return false;
  }
  if (pathname === STUDENTS.guardians || pathname.startsWith(`${STUDENTS.guardians}/`)) {
    return false;
  }
  return pathname === STUDENTS.enrolled || pathname.startsWith(`${STUDENTS.enrolled}/`);
}

const TABS = [
  { href: STUDENTS.enrolled, label: "Enrolled", isActive: isEnrolledPath },
  { href: STUDENTS.admissions, label: "Admissions" },
  { href: STUDENTS.guardians, label: "Guardians" },
];

export function StudentsHubNav() {
  return <ModuleHubNav tabs={TABS} ariaLabel="Students sections" />;
}
