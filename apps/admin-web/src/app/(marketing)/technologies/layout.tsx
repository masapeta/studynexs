import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Technologies — Noustriks",
  description:
    "Artificial intelligence, persistent memory, enterprise engineering, quantum research, and data intelligence from Noustriks.",
};

export default function TechnologiesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
