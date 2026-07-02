import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Memory Fabric — Enterprise Memory Platform | Noustriks",
  description:
    "Memory Fabric provides persistent organizational intelligence for AI agents, applications, and enterprise workflows.",
};

export default function MemoryFabricLayout({ children }: { children: React.ReactNode }) {
  return children;
}
