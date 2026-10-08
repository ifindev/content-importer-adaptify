"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { LocalTime } from "@/components/local-time";
import type { Schemas } from "@/lib/api/types";
import { cn } from "@/lib/utils";

/** The lg+ left column: every article the client can open, by group. */
export function ReviewNav({
  token,
  review,
}: {
  token: string;
  review: Schemas["ReviewPageOut"];
}) {
  const { id } = useParams<{ id?: string }>();
  const groups = [
    { title: "Waiting for your review", items: review.waiting, waiting: true },
    { title: "Upcoming", items: review.upcoming },
    { title: "Published", items: review.published },
  ];

  return (
    <nav
      aria-label="Articles"
      className="hidden w-[280px] shrink-0 overflow-y-auto px-3 pt-1 pb-6 lg:block"
    >
      {groups.map((group) => (
        <div key={group.title}>
          <h2 className="text-muted-foreground px-2.5 pt-5 pb-1.5 text-xs font-medium">
            {group.title}{" "}
            <span className="text-faint">({group.items.length})</span>
          </h2>
          {group.items.length === 0 && (
            <p className="text-faint px-2.5 py-1 text-[12.5px]">None</p>
          )}
          {group.items.map((item) => (
            <Link
              key={item.id}
              href={`/review/${token}/articles/${item.id}`}
              aria-current={item.id === id ? "page" : undefined}
              className={cn(
                "hover:bg-muted/60 focus-visible:ring-ring/50 block rounded-lg px-2.5 py-2 outline-none focus-visible:ring-3",
                item.id === id &&
                  "bg-background shadow-[0_0_0_1px_var(--border),0_1px_2px_oklch(0_0_0/0.05)]",
              )}
            >
              <span className="block text-[13.5px] leading-snug font-medium">
                {item.title}
              </span>
              <span className="text-muted-foreground mt-0.5 flex items-center gap-1.5 text-xs">
                {group.waiting && (
                  <span className="bg-primary size-1.5 rounded-full" />
                )}
                <CardMeta card={item} waiting={group.waiting} />
              </span>
            </Link>
          ))}
        </div>
      ))}
    </nav>
  );
}

export function CardMeta({
  card,
  waiting,
}: {
  card: Schemas["ArticleCard"];
  waiting?: boolean;
}) {
  if (waiting)
    return card.sent_for_review_at ? (
      <>
        Sent <LocalTime iso={card.sent_for_review_at} format="short" />
      </>
    ) : (
      <>Needs your decision</>
    );
  if (!card.publish_at_utc) return null;
  if (card.published_url)
    return <LocalTime iso={card.publish_at_utc} format="short" />;
  return (
    <>
      Publishes <LocalTime iso={card.publish_at_utc} format="short" />
    </>
  );
}
