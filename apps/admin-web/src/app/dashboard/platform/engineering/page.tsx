import { notFound } from "next/navigation";
import { isInternalDeploymentTier } from "@/lib/deployment-tier";
import EngineeringDashboardClient from "./EngineeringDashboardClient";

export default function EngineeringDashboardPage() {
  // The API is the real control (not mounted outside internal tiers); this keeps the page absent too.
  if (!isInternalDeploymentTier()) notFound();
  return <EngineeringDashboardClient />;
}
