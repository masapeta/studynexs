"use client";

import { ModuleHubNav } from "./ModuleHubNav";
import { FINANCE } from "@/lib/dashboard-routes";

const TABS = [
  { href: FINANCE.fees, label: "Fees" },
  { href: FINANCE.payroll, label: "Payroll" },
  { href: FINANCE.expenses, label: "Expenses" },
];

export function FinanceHubNav() {
  return <ModuleHubNav tabs={TABS} ariaLabel="Finance sections" />;
}
