"use client";

import { useEffect, useRef, type ReactNode } from "react";

/**
 * Pins the hero while the rest of the page slides over it, easing the hero
 * back as it gets covered. It sticks once its bottom edge reaches the viewport
 * bottom, so a hero taller than the screen is still read in full first.
 */
export function StackedHero({ children }: { children: ReactNode }) {
  const marker = useRef<HTMLDivElement>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    const start = marker.current;
    if (!el || !start) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0;

    function update() {
      frame = 0;
      if (!el || !start) return;
      const header =
        document.querySelector<HTMLElement>(".landing-header")?.offsetHeight ??
        0;
      const top = Math.min(header, window.innerHeight - el.offsetHeight);
      el.style.top = `${top}px`;
      if (reduce.matches) {
        el.style.removeProperty("--stack");
        return;
      }
      // The marker sits where the hero would be if it weren't pinned.
      const pinnedFor = top - start.getBoundingClientRect().top;
      const p = Math.min(
        Math.max(pinnedFor / (window.innerHeight * 0.8), 0),
        1,
      );
      el.style.setProperty("--stack", p.toFixed(3));
    }
    function schedule() {
      if (!frame) frame = requestAnimationFrame(update);
    }

    update();
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", schedule);
      window.removeEventListener("resize", schedule);
    };
  }, []);

  return (
    <>
      <div ref={marker} aria-hidden />
      <div ref={ref} className="hero-stack sticky z-0">
        {children}
      </div>
    </>
  );
}
