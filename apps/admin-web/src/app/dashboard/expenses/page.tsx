import { redirect } from "next/navigation";
import { FINANCE } from "@/lib/dashboard-routes";

export default function LegacyExpensesRedirect() {
  redirect(FINANCE.expenses);
}
