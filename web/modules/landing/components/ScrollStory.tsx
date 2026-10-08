"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";
import { PANEL_TINT, StepCard } from "@/modules/landing/components/StepCard";
import { STEPS } from "@/modules/landing/content";

const TITLE = "From draft to live, in four steps";

/**
 * Desktop: the rail and panel stay pinned while four ~80vh sentinels scroll
 * past; the one crossing the middle of the viewport is the active step.
 * Mobile: each step sits above its own panel, nothing pinned.
 */
export function ScrollStory() {
  const [active, setActive] = useState(0);
  const sentinels = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting)
            setActive(Number((entry.target as HTMLElement).dataset.step));
        }
      },
      { rootMargin: "-50% 0px -50% 0px" },
    );
    sentinels.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  function goTo(step: number) {
    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    sentinels.current[step]?.scrollIntoView({
      behavior: reduce ? "auto" : "smooth",
      block: "center",
    });
  }

  return (
    <section
      id="how"
      className="mx-auto max-w-[1180px] scroll-mt-20 px-5 pt-22 md:px-12 md:pt-32"
    >
      {/* Desktop */}
      <div className="relative hidden lg:block">
        <div className="sticky top-[72px] grid h-[calc(100vh-72px)] max-h-[760px] grid-cols-[0.85fr_1.15fr] gap-16 py-8">
          <div className="flex flex-col justify-between gap-10 py-6">
            <h2 className="display text-[44px] leading-[1.1]">{TITLE}</h2>
            <ol className="border-l">
              {STEPS.map((step, i) => {
                const on = i === active;
                return (
                  <li key={step.title} className="relative">
                    <span
                      aria-hidden
                      className={cn(
                        "bg-foreground absolute top-[18px] bottom-[18px] -left-px w-0.5 origin-top transition-transform duration-500",
                        on ? "scale-y-100" : "scale-y-0",
                      )}
                    />
                    <button
                      type="button"
                      onClick={() => goTo(i)}
                      aria-current={on ? "step" : undefined}
                      className="focus-visible:ring-ring/50 w-full rounded-md py-[18px] pl-7 text-left text-[19px] font-medium outline-none focus-visible:ring-3"
                    >
                      {step.title}
                    </button>
                    <div
                      className={cn(
                        "grid transition-[grid-template-rows,opacity] duration-500",
                        on
                          ? "grid-rows-[1fr] opacity-100"
                          : "grid-rows-[0fr] opacity-0",
                      )}
                    >
                      <p className="text-muted-foreground -mt-2 max-w-[400px] overflow-hidden pb-[18px] pl-7 text-[15.5px] leading-relaxed">
                        {step.text}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
          <div
            aria-hidden
            className="relative overflow-hidden rounded-[20px]"
          >
            {STEPS.map((step, i) => (
              <div
                key={step.title}
                className={cn(
                  "halftone absolute inset-0 flex items-center justify-center px-10 transition-opacity duration-500",
                  PANEL_TINT[i],
                  i === active
                    ? "opacity-100"
                    : "pointer-events-none opacity-0",
                )}
              >
                <div
                  className={cn(
                    "flex w-full justify-center transition-transform duration-500",
                    i === active ? "translate-y-0" : "translate-y-3",
                  )}
                >
                  <StepCard step={i} />
                </div>
              </div>
            ))}
          </div>
        </div>
        {/* Scroll distance: pulled up under the pinned block. */}
        <div aria-hidden className="-mt-[min(calc(100vh-72px),760px)]">
          {STEPS.map((step, i) => (
            <div
              key={step.title}
              data-step={i}
              ref={(el) => {
                sentinels.current[i] = el;
              }}
              className="h-[80vh]"
            />
          ))}
        </div>
      </div>

      {/* Mobile and tablet */}
      <div className="lg:hidden">
        <h2 className="display reveal text-[32px] leading-[1.12] md:text-[44px]">
          {TITLE}
        </h2>
        <ol>
          {STEPS.map((step, i) => (
            <li key={step.title} className="reveal mt-8 first:mt-8 md:mt-12">
              <p className="text-faint font-mono text-xs">0{i + 1}</p>
              <h3 className="mt-1.5 text-lg font-medium">{step.title}</h3>
              <p className="text-muted-foreground mt-1.5 text-[15px] leading-relaxed">
                {step.text}
              </p>
              <div
                aria-hidden
                className={cn(
                  "halftone mt-4 flex min-h-[340px] items-center justify-center rounded-2xl px-4 py-7",
                  PANEL_TINT[i],
                )}
              >
                <StepCard step={i} />
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
