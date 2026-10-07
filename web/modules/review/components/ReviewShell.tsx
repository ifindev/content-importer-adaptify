import type { Schemas } from "@/lib/api/types";
import { getReview } from "@/modules/review/data";

import { ReviewNav } from "./ReviewNav";

/**
 * Header plus, at lg+, the article list beside the page. Each review page
 * renders it (not the layout) so the segment's not-found and error files
 * still catch an invalid token or a rate limit.
 */
export async function ReviewShell({
  token,
  children,
}: {
  token: string;
  children: (review: Schemas["ReviewPageOut"]) => React.ReactNode;
}) {
  const review = await getReview(token);

  return (
    <div className="bg-app flex min-h-svh flex-col">
      <header className="bg-background flex h-14 shrink-0 items-center gap-3 border-b px-4 lg:px-6">
        <span
          aria-hidden
          className="bg-muted text-foreground/70 flex size-7 items-center justify-center rounded-lg text-xs font-semibold uppercase"
        >
          {review.site_name.charAt(0)}
        </span>
        <div className="flex min-w-0 items-baseline gap-2.5">
          <span className="truncate text-[15px] font-semibold tracking-tight">
            {review.site_name}
          </span>
          <span className="text-muted-foreground shrink-0 text-[13px]">
            Article review
          </span>
        </div>
      </header>
      <div className="flex min-h-0 flex-1">
        <ReviewNav token={token} review={review} />
        {children(review)}
      </div>
    </div>
  );
}
