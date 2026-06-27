import { redirect } from "next/navigation";
import { FINANCE } from "@/lib/dashboard-routes";

export default function LegacyFeesRedirect() {
  redirect(FINANCE.fees);
}
