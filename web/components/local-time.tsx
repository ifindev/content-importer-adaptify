"use client";

import { useSyncExternalStore } from "react";

const FORMATS = {
  date: { month: "short", day: "numeric", year: "numeric" },
  short: { month: "short", day: "numeric" },
  datetime: {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  },
} satisfies Record<string, Intl.DateTimeFormatOptions>;

const subscribe = () => () => {};

/**
 * Renders a UTC timestamp in the viewer's time zone. The server pass renders
 * UTC; the client re-renders in local time after hydration.
 */
export function LocalTime({
  iso,
  format = "date",
}: {
  iso: string;
  format?: keyof typeof FORMATS;
}) {
  const timeZone = useSyncExternalStore(
    subscribe,
    () => undefined,
    () => "UTC",
  );
  return (
    <time dateTime={iso} suppressHydrationWarning>
      {new Intl.DateTimeFormat("en-US", {
        ...FORMATS[format],
        timeZone,
      }).format(new Date(iso))}
    </time>
  );
}
