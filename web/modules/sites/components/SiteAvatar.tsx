import { cn } from "@/lib/utils";

export function SiteAvatar({
  label,
  size = "sm",
}: {
  label: string;
  size?: "sm" | "lg";
}) {
  return (
    <span
      aria-hidden
      className={cn(
        "bg-muted text-foreground/70 flex shrink-0 items-center justify-center font-semibold uppercase",
        size === "sm"
          ? "size-5 rounded-[5px] text-[11px]"
          : "size-8 rounded-lg text-[13px]",
      )}
    >
      {label.charAt(0)}
    </span>
  );
}
