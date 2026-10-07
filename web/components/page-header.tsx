import { SidebarTrigger } from "@/components/ui/sidebar";

/**
 * The page title row. Below md it doubles as the app bar: menu button, title,
 * and the page's actions, as on the mobile frames.
 */
export function PageHeader({
  title,
  subtitle,
  children,
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <header className="border-border flex min-h-[52px] items-center gap-2 border-b px-1 md:flex-wrap md:justify-between md:gap-4 md:border-0 md:px-7 md:pt-[22px]">
      <SidebarTrigger className="size-11 md:hidden" aria-label="Open menu" />
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-[15px] leading-tight font-semibold tracking-tight md:text-xl">
          {title}
        </h1>
        {subtitle && (
          <p className="text-muted-foreground mt-0.5 hidden text-[13px] md:block">
            {subtitle}
          </p>
        )}
      </div>
      {children && (
        <div className="flex shrink-0 items-center gap-2 pr-2 md:pr-0">
          {children}
        </div>
      )}
    </header>
  );
}
