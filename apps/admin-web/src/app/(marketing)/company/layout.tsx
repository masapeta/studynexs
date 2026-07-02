import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Company — Noustriks",
  description:
    "Noustriks is a deep technology company building intelligent platforms at the intersection of AI, memory, and enterprise infrastructure.",
};

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  return children;
}
