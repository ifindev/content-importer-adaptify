export function ReviewArticlePage({
  token,
  articleId,
}: {
  token: string;
  articleId: string;
}) {
  return (
    <h1>
      Review {token} — article {articleId}
    </h1>
  );
}
