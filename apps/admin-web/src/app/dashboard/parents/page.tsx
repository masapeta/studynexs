import { redirect } from "next/navigation";
import { STUDENTS } from "@/lib/dashboard-routes";

export default function LegacyParentsRedirect() {
  redirect(STUDENTS.guardians);
}
