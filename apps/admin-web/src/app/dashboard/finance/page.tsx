import { redirect } from "next/navigation";
import { FINANCE } from "@/lib/dashboard-routes";

export default async function FinanceIndexPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const qs = new URLSearchParams(
    Object.entries(await searchParams).flatMap(([k, v]) => (Array.isArray(v) ? v.map((x) => [k, x]) : v ? [[k, v]] : []))
  ).toString();
  redirect(qs ? `${FINANCE.fees}?${qs}` : FINANCE.fees);
}
