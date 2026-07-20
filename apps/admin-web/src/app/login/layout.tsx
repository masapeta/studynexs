import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/marketing-tokens.css";
import "@/styles/marketing.css";
import { SkipLink } from "@/components/a11y/SkipLink";
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
      <SkipLink label="Skip to sign in" />
      <MarketingBackground />
      <MarketingNav />
      <div className="mkt-shell" id="main-content" tabIndex={-1}>
        {children}
      </div>
    </div>
  );
}
