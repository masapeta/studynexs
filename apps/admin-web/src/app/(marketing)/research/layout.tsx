import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Research — Noustriks",
  description:
    "Noustriks Research in artificial intelligence, persistent memory, responsible AI, quantum computing, and enterprise intelligence.",
};

export default function ResearchLayout({ children }: { children: React.ReactNode }) {
  return children;
}
