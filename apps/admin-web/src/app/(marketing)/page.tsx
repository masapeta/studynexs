import { AIStorySection } from "@/components/marketing/AIStorySection";
import { TrustBar } from "@/components/marketing/TrustBar";
import {
  CTASection,
  FeaturesSection,
  HeroSection,
  MarketingFooter,
  StatsSection,
  TestimonialsSection,
} from "@/components/marketing/Sections";

export default function HomePage() {
  return (
    <main>
      <HeroSection />
      <TrustBar />
      <StatsSection />
      <FeaturesSection />
      <AIStorySection />
      <TestimonialsSection />
      <CTASection />
      <MarketingFooter />
    </main>
  );
}
