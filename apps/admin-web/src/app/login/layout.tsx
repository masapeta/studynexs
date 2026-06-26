import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/marketing.css";
import { MarketingBackground, MarketingNav } from "@/components/marketing/MarketingShell";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-marketing",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sign in — StudyNexs",
  description: "Sign in to your StudyNexs school portal",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className={`mkt ${inter.variable}`}>
      <MarketingBackground />
      <MarketingNav />
      <div className="mkt-shell">{children}</div>
    </div>
  );
}
