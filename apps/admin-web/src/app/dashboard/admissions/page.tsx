import { redirect } from "next/navigation";
import { STUDENTS } from "@/lib/dashboard-routes";

export default function LegacyAdmissionsRedirect() {
  redirect(STUDENTS.admissions);
}
