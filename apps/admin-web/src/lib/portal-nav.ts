/** Shared portal bottom-nav configs (icons + labels). One source of truth so the
 *  nav is identical across every page in a portal. */
import { Bell, Home, Users, Wallet } from "lucide-react";
import type { NavItem } from "@/components/PortalShell";

export const PARENT_NAV: NavItem[] = [
  { href: "/parent", label: "Home", icon: Home },
  { href: "/parent/children", label: "Children", icon: Users },
  { href: "/parent/notices", label: "Notices", icon: Bell },
  { href: "/parent/fees", label: "Fees", icon: Wallet },
];
