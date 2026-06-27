import { redirect } from "next/navigation";
import { TEACHING } from "@/lib/dashboard-routes";

export default function LegacyEvaluateRedirect({
  params,
}: {
  params: { examId: string };
}) {
  redirect(TEACHING.evaluate(params.examId));
}
