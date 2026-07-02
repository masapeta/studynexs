import "@/styles/sn-app-bundle.css";
import { ParentPortalShell } from "./ParentPortalShell";

export default function ParentLayout({ children }: { children: React.ReactNode }) {
  return <ParentPortalShell>{children}</ParentPortalShell>;
}
