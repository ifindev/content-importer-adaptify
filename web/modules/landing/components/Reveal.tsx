"use client";

import { useEffect } from "react";

/**
 * Fades sections in as they scroll into view. Elements already on screen at
 * load are left alone (the hero has its own load-in); everything below the
 * fold starts hidden and gets `reveal-in` once. Renders nothing.
 */
export function Reveal() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const targets = document.querySelectorAll<HTMLElement>(
      ".landing .reveal, .landing .seq > *",
    );
    const observer = new IntersectionObserver(
      (entries) => {
        // Elements entering together (cards in a row) cascade in.
        let batch = 0;
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const el = entry.target as HTMLElement;
          el.style.transitionDelay = `${Math.min(batch, 4) * 90}ms`;
          batch++;
          // Drop the delay afterwards so hover transitions stay instant.
          el.addEventListener(
            "transitionend",
            () => el.style.removeProperty("transition-delay"),
            { once: true },
          );
          el.classList.add("reveal-in");
          observer.unobserve(el);
        }
      },
      // The huge top margin also reveals anything a jump (anchor link,
      // End key) scrolled past without it ever crossing the viewport.
      { rootMargin: "100000px 0px -15% 0px" },
    );

    for (const el of targets) {
      if (el.getBoundingClientRect().top < window.innerHeight) continue;
      el.classList.add("reveal-hide");
      observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  return null;
}
