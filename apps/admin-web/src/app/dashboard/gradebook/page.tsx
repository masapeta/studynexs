import { redirect } from "next/navigation";
import { TEACHING } from "@/lib/dashboard-routes";

export default function LegacyGradebookRedirect() {
  redirect(TEACHING.gradebook);
}
