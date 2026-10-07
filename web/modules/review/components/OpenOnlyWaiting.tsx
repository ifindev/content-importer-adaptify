"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

/** At lg+, with exactly one article waiting, skip the empty reader. */
export function OpenOnlyWaiting({ href }: { href: string }) {
  const router = useRouter();
  useEffect(() => {
    if (window.matchMedia("(min-width: 1024px)").matches) router.replace(href);
  }, [href, router]);
  return null;
}
