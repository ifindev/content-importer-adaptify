"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { mergeQueryString } from "@/lib/query-string";

export function useFilterParams() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function setParams(patch: Record<string, string | undefined>) {
    const query = mergeQueryString(searchParams, patch);
    router.push(query ? `${pathname}?${query}` : pathname);
  }

  return { setParams };
}
