import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Products — Noustriks",
  description:
    "StudyNexs and Memory Fabric — flagship intelligent platforms from Noustriks for education and enterprise.",
};

export default function ProductsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
