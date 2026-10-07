"use client";

export default function Error({ error }: { error: Error }) {
  const message =
    error.message === "rate_limited"
      ? "Too many requests. Try again in a minute."
      : "Something went wrong.";

  return (
    <div className="p-4">
      <p className="text-sm">{message}</p>
    </div>
  );
}
