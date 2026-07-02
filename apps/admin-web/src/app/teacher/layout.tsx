import "@/styles/sn-app-bundle.css";
import { TeacherPortalShell } from "./TeacherPortalShell";

export default function TeacherLayout({ children }: { children: React.ReactNode }) {
  return <TeacherPortalShell>{children}</TeacherPortalShell>;
}
