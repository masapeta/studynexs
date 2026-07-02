import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Technology — Noustriks",
  description:
    "Artificial intelligence, memory systems, quantum research, cloud engineering, and data platforms from Noustriks.",
};

export default function TechnologyLayout({ children }: { children: React.ReactNode }) {
  return children;
}
