import { redirect } from "next/navigation";
import { TEACHING } from "@/lib/dashboard-routes";

export default function LegacyExamsRedirect() {
  redirect(TEACHING.exams);
}
