import { redirect } from "next/navigation";
import { DASHBOARD } from "@/lib/dashboard-routes";

export default function TeacherHomeRedirect() {
  redirect(DASHBOARD);
}
