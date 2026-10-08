import { TODAY, WITH_US } from "@/modules/landing/content";

function Column({
  label,
  items,
  muted,
}: {
  label: string;
  items: readonly string[];
  muted?: boolean;
}) {
  return (
    <div className="reveal">
      <h3
        className={`pb-3 font-mono text-[12.5px] tracking-[0.06em] uppercase ${muted ? "text-faint" : ""}`}
      >
        {label}
      </h3>
      <ul className="border-b">
        {items.map((t) => (
          <li
            key={t}
            className={`border-t py-3.5 text-[15px] md:py-4 md:text-base ${muted ? "text-muted-foreground" : ""}`}
          >
            {t}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ProblemSection() {
  return (
    <section className="mx-auto max-w-[1180px] px-5 pt-22 md:px-12 md:pt-32">
      <div className="reveal">
        <h2 className="display max-w-[820px] text-[32px] leading-[1.12] md:text-[44px] md:leading-[1.1]">
          No more “did the client approve this version?”
        </h2>
        <p className="text-muted-foreground mt-4 max-w-[520px] text-base leading-relaxed md:text-[17px]">
          Content work stalls between the writer and the website. Content
          Importer closes that gap.
        </p>
      </div>
      <div className="mt-9 grid gap-8 md:mt-14 md:grid-cols-2 md:gap-12">
        <Column label="Today" items={TODAY} muted />
        <Column label="With Content Importer" items={WITH_US} />
      </div>
    </section>
  );
}
