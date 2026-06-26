import {
  CTASection,
  FeaturesSection,
  HeroSection,
  MarketingFooter,
  RolesSection,
  StatsSection,
  TestimonialsSection,
} from "@/components/marketing/Sections";

export default function HomePage() {
  return (
    <main>
      <HeroSection />
      <StatsSection />
      <FeaturesSection />
      <RolesSection />
      <TestimonialsSection />
      <CTASection />
      <MarketingFooter />
    </main>
  );
}
