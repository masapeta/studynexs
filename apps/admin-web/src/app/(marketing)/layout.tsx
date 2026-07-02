import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/marketing-tokens.css";
import "@/styles/marketing.css";
import { MarketingBackground, MarketingNav } from "@/components/marketing/MarketingShell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-marketing",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Noustriks — Engineering Intelligent Systems",
  description:
    "Noustriks builds intelligent platforms — StudyNexs for education, Memory Fabric for enterprise — at the intersection of AI, memory, and infrastructure.",
};

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`mkt ${inter.variable}`}>
      <MarketingBackground />
      <MarketingNav />
      <div className="mkt-shell">{children}</div>
    </div>
  );
}
