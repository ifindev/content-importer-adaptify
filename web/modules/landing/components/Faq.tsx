import { Plus } from "lucide-react";

import { FAQ } from "@/modules/landing/content";

export function Faq() {
  return (
    <section
      id="faq"
      className="mx-auto grid max-w-[1180px] scroll-mt-20 gap-6 px-5 pt-22 md:grid-cols-[0.8fr_1.2fr] md:gap-16 md:px-12 md:pt-32"
    >
      <h2 className="display reveal text-[32px] leading-[1.12] md:text-[44px]">
        Questions, answered
      </h2>
      <div className="reveal border-b">
        {FAQ.map((item, i) => (
          <details key={item.q} className="faq border-t" open={i === 0}>
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-5 text-base font-medium md:py-[22px]">
              {item.q}
              <Plus
                aria-hidden
                className="faq-icon text-faint size-4 shrink-0"
              />
            </summary>
            <p className="text-muted-foreground max-w-[640px] pb-5 text-[15px] leading-relaxed md:pb-[22px]">
              {item.a}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}
