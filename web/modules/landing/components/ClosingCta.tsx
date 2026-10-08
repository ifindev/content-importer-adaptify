import { ArrowRight } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { LINKS } from "@/modules/landing/content";

export function ClosingCta() {
  return (
    <section className="mx-auto max-w-[1180px] px-3 pt-22 pb-12 md:px-12 md:pt-32 md:pb-24">
      <div className="halftone reveal rounded-[20px] px-6 py-14 text-center text-white md:px-12 md:py-24">
        <div
          className="halftone-scrim"
          style={{ background: "oklch(0.25 0.16 266 / 0.35)" }}
        />
        <h2 className="display text-[36px] leading-[1.08] md:text-[56px] md:leading-[1.05]">
          Stop chasing approvals
        </h2>
        <p className="mx-auto mt-3 max-w-[460px] text-[15.5px] leading-relaxed text-white/85 md:mt-4 md:text-[17px]">
          Try it with a sample agency account: import an article, send it for
          review and schedule it.
        </p>
        <div className="mt-7 flex flex-col justify-center gap-2.5 sm:flex-row md:mt-8">
          <Link
            href={LINKS.demo}
            className={cn(
              buttonVariants(),
              "group text-foreground h-11 bg-white px-5 text-[15px] hover:bg-white/90 sm:h-10",
            )}
          >
            Try the live demo
            <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
          </Link>
          <Link
            href={LINKS.signIn}
            className={cn(
              buttonVariants({ variant: "outline" }),
              "h-11 border-white/50 bg-transparent px-5 text-[15px] text-white hover:bg-white/10 hover:text-white sm:h-10",
            )}
          >
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}
