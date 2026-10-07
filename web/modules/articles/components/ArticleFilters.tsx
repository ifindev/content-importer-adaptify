"use client";

import { ChevronDown, Search } from "lucide-react";
import { useEffect, useState } from "react";

import { statusLabel } from "@/components/status-badge";
import { useFilterParams } from "@/hooks/use-filter-params";

import { STATUS_OPTIONS } from "./status-options";

export function ArticleFilters({
  status,
  query,
  counts,
}: {
  status: string | undefined;
  query: string;
  counts: Record<string, number>;
}) {
  const { setParams } = useFilterParams();
  const [search, setSearch] = useState(query);

  useEffect(() => {
    if (search === query) return;
    const timer = setTimeout(() => setParams({ q: search || undefined }), 300);
    return () => clearTimeout(timer);
  }, [search, query, setParams]);

  return (
    <div className="flex items-center gap-2 border-b px-4 py-3 md:flex-wrap md:border-0 md:px-7 md:pt-[18px] md:pb-2.5">
      <label className="relative min-w-0 flex-1 md:w-[260px] md:flex-none">
        <Search className="text-faint pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2" />
        <input
          type="search"
          aria-label="Search articles"
          placeholder="Search articles"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border-input focus-visible:border-primary/50 focus-visible:ring-primary/12 h-10 w-full rounded-lg border bg-transparent pr-2.5 pl-8 text-[15px] shadow-xs outline-none focus-visible:ring-3 md:h-8 md:text-[13px]"
        />
      </label>
      <label className="relative inline-flex shrink-0 items-center">
        <span className="text-muted-foreground pointer-events-none absolute left-2.5 text-[13px] max-md:sr-only">
          Status
        </span>
        <select
          value={status ?? ""}
          onChange={(e) => setParams({ status: e.target.value || undefined })}
          className="border-input focus-visible:border-primary/50 focus-visible:ring-primary/12 h-10 w-[104px] cursor-pointer appearance-none truncate rounded-lg border bg-transparent pr-7 pl-2.5 text-[15px] font-medium shadow-xs outline-none focus-visible:ring-3 md:h-8 md:w-auto md:pl-[58px] md:text-[13px]"
        >
          <option value="">All</option>
          {STATUS_OPTIONS.map((value) => (
            <option key={value} value={value}>
              {value === "needs_attention"
                ? "Needs attention"
                : statusLabel(value)}{" "}
              · {counts[value] ?? 0}
            </option>
          ))}
        </select>
        <ChevronDown className="text-faint pointer-events-none absolute right-2.5 size-3.5" />
      </label>
    </div>
  );
}
