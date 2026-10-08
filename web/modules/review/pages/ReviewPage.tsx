import { ExternalLink, Inbox } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import type { Schemas } from "@/lib/api/types";
import { OpenOnlyWaiting } from "@/modules/review/components/OpenOnlyWaiting";
import { CardMeta } from "@/modules/review/components/ReviewNav";
import { ReviewShell } from "@/modules/review/components/ReviewShell";

const CARD = "rounded-xl border bg-card shadow-[0_1px_2px_oklch(0_0_0/0.03)]";

export function ReviewPage({ token }: { token: string }) {
  return (
    <ReviewShell token={token}>
      {(review) => {
        const total =
          review.waiting.length +
          review.upcoming.length +
          review.published.length;
        return (
          <>
            {review.waiting.length === 1 && (
              <OpenOnlyWaiting
                href={`/review/${token}/articles/${review.waiting[0].id}`}
              />
            )}
            {/* Below lg: the list is the page. */}
            <div className="mx-auto flex w-full max-w-xl flex-col gap-6 px-4 py-5 lg:hidden">
              {total === 0 ? (
                <AllEmpty />
              ) : (
                <>
                  <Group
                    title="Waiting for your review"
                    count={review.waiting.length}
                    empty="Nothing waiting for you right now."
                  >
                    {review.waiting.map((card) => (
                      <div
                        key={card.id}
                        className="border-t px-4 py-3.5 first:border-t-0"
                      >
                        <div className="text-[15px] font-medium">
                          {card.title}
                        </div>
                        <Link
                          href={`/review/${token}/articles/${card.id}`}
                          className={buttonVariants({
                            className: "mt-3 h-10 w-full",
                          })}
                        >
                          Read and review
                        </Link>
                      </div>
                    ))}
                  </Group>
                  <CardGroup
                    token={token}
                    title="Upcoming"
                    cards={review.upcoming}
                    empty="Nothing scheduled yet."
                  />
                  <CardGroup
                    token={token}
                    title="Published"
                    cards={review.published}
                    empty="Nothing published yet."
                  />
                </>
              )}
            </div>
            {/* lg+: the list sits in the left column; the reader is empty. */}
            <main className="bg-background m-3 ml-0 hidden flex-1 items-center justify-center rounded-xl border p-8 text-center lg:flex">
              {total === 0 ? (
                <AllEmpty />
              ) : (
                <div>
                  <Inbox className="text-faint mx-auto mb-3 size-6" />
                  <p className="text-muted-foreground text-sm">
                    Choose an article to read.
                  </p>
                </div>
              )}
            </main>
          </>
        );
      }}
    </ReviewShell>
  );
}

function AllEmpty() {
  return (
    <div className="py-10 text-center">
      <Inbox className="text-faint mx-auto mb-3 size-6" />
      <h1 className="text-[15px] font-semibold">No articles yet</h1>
      <p className="text-muted-foreground mt-1 text-[13.5px]">
        The agency hasn&apos;t sent anything for review. Check back later.
      </p>
    </div>
  );
}

function Group({
  title,
  count,
  empty,
  children,
}: {
  title: string;
  count: number;
  empty: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-2.5 flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">{title}</h2>
        <span className="text-muted-foreground text-[12.5px]">{count}</span>
      </div>
      <div className={CARD}>
        {count === 0 ? (
          <p className="text-muted-foreground px-4 py-3.5 text-[13px]">
            {empty}
          </p>
        ) : (
          children
        )}
      </div>
    </section>
  );
}

function CardGroup({
  token,
  title,
  cards,
  empty,
}: {
  token: string;
  title: string;
  cards: Schemas["ArticleCard"][];
  empty: string;
}) {
  return (
    <Group title={title} count={cards.length} empty={empty}>
      {cards.map((card) => (
        <div
          key={card.id}
          className="flex items-center gap-3 border-t px-4 py-3 first:border-t-0"
        >
          <Link
            href={`/review/${token}/articles/${card.id}`}
            className="min-w-0 flex-1"
          >
            <span className="block text-sm font-medium">{card.title}</span>
            <span className="text-muted-foreground text-[12.5px]">
              <CardMeta card={card} />
            </span>
          </Link>
          {card.published_url && (
            <a
              href={card.published_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-foreground/65 hover:text-foreground inline-flex shrink-0 items-center gap-1 text-[13px]"
            >
              View <ExternalLink className="size-3" />
            </a>
          )}
        </div>
      ))}
    </Group>
  );
}
