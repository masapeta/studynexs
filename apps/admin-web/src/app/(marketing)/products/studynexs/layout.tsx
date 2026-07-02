import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "StudyNexs — AI School Operating System | Noustriks",
  description:
    "StudyNexs is the AI Operating System for Modern Schools — intelligent administration, teaching, learning, and family communication.",
};

export default function StudyNexsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
