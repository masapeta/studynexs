import "@/styles/sn-app-bundle.css";
import { StudentPortalShell } from "./StudentPortalShell";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return <StudentPortalShell>{children}</StudentPortalShell>;
}
