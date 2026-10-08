"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { DayPicker } from "react-day-picker";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * A month grid on the app's tokens. Days the caller disables stay on the
 * normal background and turn into faint text, like in the design.
 */
function Calendar({
  className,
  classNames,
  ...props
}: React.ComponentProps<typeof DayPicker>) {
  return (
    <DayPicker
      showOutsideDays
      weekStartsOn={0}
      className={cn("p-1", className)}
      classNames={{
        root: "w-fit",
        months: "relative flex flex-col",
        month: "flex flex-col gap-2",
        month_caption: "flex h-8 items-center justify-center",
        caption_label: "text-[13px] font-medium",
        nav: "absolute inset-x-0 top-0 flex h-8 items-center justify-between",
        button_previous: cn(
          buttonVariants({ variant: "ghost", size: "icon" }),
          "size-8 text-muted-foreground aria-disabled:opacity-40",
        ),
        button_next: cn(
          buttonVariants({ variant: "ghost", size: "icon" }),
          "size-8 text-muted-foreground aria-disabled:opacity-40",
        ),
        month_grid: "border-collapse",
        weekdays: "flex",
        weekday:
          "text-muted-foreground w-9 text-center text-[12px] font-normal",
        week: "mt-1 flex",
        day: "size-9 p-0 text-center text-[13px]",
        day_button: cn(
          "focus-visible:ring-ring/50 inline-flex size-9 items-center justify-center rounded-lg tabular-nums outline-none hover:bg-muted focus-visible:ring-3",
        ),
        selected:
          "[&>button]:bg-primary [&>button]:text-primary-foreground [&>button:hover]:bg-primary",
        today: "[&>button]:font-semibold",
        outside: "text-faint",
        disabled:
          "text-faint [&>button]:cursor-not-allowed [&>button]:bg-transparent [&>button:hover]:bg-transparent",
        hidden: "invisible",
        ...classNames,
      }}
      components={{
        Chevron: ({ orientation, className: chevronClass }) =>
          orientation === "left" ? (
            <ChevronLeft className={cn("size-4", chevronClass)} />
          ) : (
            <ChevronRight className={cn("size-4", chevronClass)} />
          ),
      }}
      {...props}
    />
  );
}

export { Calendar };
