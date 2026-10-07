import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div
      aria-busy="true"
      aria-label="Loading articles"
      className="flex flex-col gap-3.5 px-4 py-4 md:px-7 md:py-[22px]"
    >
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-3 w-28" />
      <div className="my-2 flex gap-2">
        <Skeleton className="h-8 w-full max-w-[260px]" />
        <Skeleton className="h-8 w-28" />
      </div>
      {[92, 86, 90, 80, 88].map((w) => (
        <Skeleton key={w} className="h-3.5" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}
