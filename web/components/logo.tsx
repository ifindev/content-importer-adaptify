import { ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils";

const SIZES = {
  sm: "size-6 rounded-[7px] [&_svg]:size-3.5",
  md: "size-7 rounded-[8px] [&_svg]:size-3.5",
  lg: "size-9 rounded-[10px] [&_svg]:size-[18px]",
} as const;

/** The app mark: a dark rounded square with an up-right arrow. */
export function LogoMark({
  size = "sm",
  className,
}: {
  size?: keyof typeof SIZES;
  className?: string;
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "bg-foreground text-background flex shrink-0 items-center justify-center",
        SIZES[size],
        className,
      )}
    >
      <ArrowUpRight strokeWidth={2.5} />
    </span>
  );
}
