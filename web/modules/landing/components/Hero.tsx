import { ArrowRight } from "lucide-react";
import Link from "next/link";
import type { CSSProperties } from "react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { DotMatrix } from "@/modules/landing/components/DotMatrix";
import { DARK_BUTTON, LINKS, STATS } from "@/modules/landing/content";

const delay = (d: number) => ({ "--d": d }) as CSSProperties;

export function Hero() {
  return (
    <section className="mx-auto grid max-w-[1180px] gap-10 px-5 pt-10 pb-10 md:px-12 md:pt-24 md:pb-24 lg:grid-cols-[1.1fr_0.9fr] lg:gap-12">
      <div>
        <h1
          className="display rise text-[42px] leading-[1.06] md:text-[62px]"
          style={delay(0)}
        >
          Client-approved articles, published on schedule
        </h1>
        <p
          className="rise text-muted-foreground mt-4 max-w-[520px] text-base leading-relaxed md:text-lg"
          style={delay(1)}
        >
          Bring in articles from your writers, Google Docs or Word. Clients
          approve from a private link, and approved posts go live on WordPress
          on the date you pick.
        </p>
        <div
          className="rise mt-7 flex flex-col gap-2.5 sm:flex-row sm:items-center sm:gap-3 md:mt-9"
          style={delay(2)}
        >
          <Link
            href={LINKS.demo}
            className={cn(
              buttonVariants(),
              "group h-11 px-5 text-[15px] sm:h-10",
              DARK_BUTTON,
            )}
          >
            Try the live demo
            <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#how"
            className={cn(
              buttonVariants({ variant: "ghost" }),
              "h-11 px-3 text-[15px] sm:h-10",
            )}
          >
            See how it works
          </a>
        </div>
        <div
          className="rise mt-10 grid max-w-[460px] grid-cols-2 md:mt-16"
          style={delay(3)}
        >
          {STATS.map((s, i) => (
            <div
              key={s.label}
              className={cn(i > 0 && "border-l pl-5 md:pl-10")}
            >
              <p className="font-mono text-[28px] tracking-tight md:text-[34px]">
                {s.value}
              </p>
              <p className="text-muted-foreground mt-1 text-[13.5px] md:text-[14.5px]">
                {s.label}
              </p>
            </div>
          ))}
        </div>
      </div>
      {/* As tall as the text column: the box stretches, the square fits its height. */}
      <div className="relative hidden lg:block">
        <DotMatrix className="absolute inset-y-0 right-0 grid h-full" />
      </div>
    </section>
  );
}
