import { redirect } from "next/navigation";
import { PLATFORM } from "@/lib/dashboard-routes";

export default function PlatformHubPage() {
  redirect(PLATFORM.engineering);
}
