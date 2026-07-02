import { CompanyFocusSection } from "@/components/marketing/CompanyFocusSection";
import { HomeCTASection } from "@/components/marketing/HomeCTASection";
import { HomeHeroSection } from "@/components/marketing/HomeHeroSection";
import { HomeProductsSection } from "@/components/marketing/HomeProductsSection";
import { AboutNoustriksSection, VisionSection } from "@/components/marketing/NoustriksSections";
import { TrustBar } from "@/components/marketing/TrustBar";
import { MarketingFooter } from "@/components/marketing/Sections";

export default function HomePage() {
  return (
    <main>
      <HomeHeroSection />
      <TrustBar />
      <HomeProductsSection />
      <CompanyFocusSection />
      <AboutNoustriksSection />
      <VisionSection />
      <HomeCTASection />
      <MarketingFooter />
    </main>
  );
}
