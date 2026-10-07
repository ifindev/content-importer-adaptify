import { ArrowLeft } from "lucide-react";
import Link from "next/link";

import { PROSE } from "@/components/prose";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { DecisionPanel } from "@/modules/review/components/DecisionPanel";
import { ReviewShell } from "@/modules/review/components/ReviewShell";
import { getReviewArticle } from "@/modules/review/data";

export async function ReviewArticlePage({
  token,
  articleId,
}: {
  token: string;
  articleId: string;
}) {
  const article = await getReviewArticle(token, articleId);

  return (
    <ReviewShell token={token}>
      {(review) => {
        const card = [
          ...review.waiting,
          ...review.upcoming,
          ...review.published,
        ].find((c) => c.id === article.id);
        return (
          <main className="bg-background flex min-w-0 flex-1 flex-col lg:m-3 lg:ml-0 lg:flex-row lg:overflow-hidden lg:rounded-xl lg:border lg:shadow-[0_1px_3px_oklch(0_0_0/0.04)]">
            <article className="min-w-0 flex-1 overflow-y-auto px-5 pt-3 pb-8 lg:px-14 lg:pt-12 lg:pb-16">
              <Link
                href={`/review/${token}`}
                className={cn(
                  buttonVariants({ variant: "ghost" }),
                  "text-muted-foreground mb-3 -ml-3 h-11 lg:hidden",
                )}
              >
                <ArrowLeft /> All articles
              </Link>
              <div className="mx-auto max-w-[640px]">
                <h1 className="text-[26px] leading-tight font-semibold tracking-tight lg:text-[30px]">
                  {article.title}
                </h1>
                <div
                  className={cn("mt-6 lg:mt-8", PROSE)}
                  // Sanitized server-side (nh3) before it is stored.
                  dangerouslySetInnerHTML={{ __html: article.body_html }}
                />
              </div>
            </article>
            <DecisionPanel token={token} article={article} card={card} />
          </main>
        );
      }}
    </ReviewShell>
  );
}
