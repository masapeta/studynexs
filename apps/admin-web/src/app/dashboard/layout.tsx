import "@/styles/sn-app-bundle.css";
import { DashboardShell } from "./DashboardShell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>;
}
