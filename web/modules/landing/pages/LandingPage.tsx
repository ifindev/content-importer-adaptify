import "@/modules/landing/landing.css";

import { Bento } from "@/modules/landing/components/Bento";
import { ClosingCta } from "@/modules/landing/components/ClosingCta";
import { Faq } from "@/modules/landing/components/Faq";
import { Hero } from "@/modules/landing/components/Hero";
import { LandingFooter } from "@/modules/landing/components/LandingFooter";
import { LandingHeader } from "@/modules/landing/components/LandingHeader";
import { Reveal } from "@/modules/landing/components/Reveal";
import { ProblemSection } from "@/modules/landing/components/ProblemSection";
import { ProductWindow } from "@/modules/landing/components/ProductWindow";
import { StackedHero } from "@/modules/landing/components/StackedHero";
import { ScrollStory } from "@/modules/landing/components/ScrollStory";
import { displayFont } from "@/modules/landing/fonts";

export default function LandingPage() {
  return (
    <div
      className={`landing ${displayFont.variable} bg-background text-foreground text-[15px]`}
    >
      <LandingHeader />
      <main>
        <StackedHero>
          <Hero />
        </StackedHero>
        <div className="bg-background relative z-10">
          <ProductWindow />
          <ProblemSection />
          <ScrollStory />
          <Bento />
          <Faq />
          <ClosingCta />
        </div>
      </main>
      <LandingFooter />
      <Reveal />
    </div>
  );
}
