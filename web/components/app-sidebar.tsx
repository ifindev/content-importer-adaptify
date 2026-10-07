"use client";

import {
  ArrowUpRight,
  ChartColumn,
  Download,
  FileText,
  Globe,
  LogOut,
} from "lucide-react";
import Link from "next/link";
import { useParams, usePathname } from "next/navigation";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import { logout } from "@/modules/auth/repository/auth.mutations";
import { SiteSwitcher } from "@/modules/sites/components/SiteSwitcher";

const NAV_ITEMS = [
  { path: "import", label: "Import", icon: Download },
  { path: "articles", label: "Articles", icon: FileText },
  { path: "report", label: "Report", icon: ChartColumn },
];

const NAV_BUTTON =
  "text-foreground/65 h-8 gap-2.5 rounded-[7px] px-2.5 text-[13.5px] font-medium [&_svg]:text-faint data-active:bg-background data-active:text-foreground data-active:[&_svg]:text-foreground data-active:shadow-[0_0_0_1px_var(--border),0_1px_2px_oklch(0_0_0/0.05)]";

type ShellSite = { id: string; wp_base_url: string; connection_ok: boolean };

export function AppSidebar({
  email,
  sites,
}: {
  email: string | null;
  sites: ShellSite[];
}) {
  const pathname = usePathname();
  const { siteId } = useParams<{ siteId?: string }>();
  const { setOpenMobile } = useSidebar();
  const navSite = siteId ?? sites[0]?.id;

  return (
    <Sidebar variant="inset" collapsible="icon">
      <SidebarHeader className="gap-3.5 px-2.5 pt-3.5">
        <div className="flex items-center gap-2.5 px-2 pt-1 group-data-[collapsible=icon]:px-0">
          <span className="bg-foreground text-background flex size-6 shrink-0 items-center justify-center rounded-[7px]">
            <ArrowUpRight className="size-3.5" strokeWidth={2.5} />
          </span>
          <span className="truncate text-[13.5px] font-semibold tracking-tight group-data-[collapsible=icon]:hidden">
            Content Importer
          </span>
        </div>
        {sites.length > 0 && <SiteSwitcher sites={sites} currentId={siteId} />}
      </SidebarHeader>
      <SidebarContent className="px-2.5 pt-1">
        <SidebarMenu className="gap-0.5">
          {navSite &&
            NAV_ITEMS.map(({ path, label, icon: Icon }) => {
              const href = `/sites/${navSite}/${path}`;
              return (
                <SidebarMenuItem key={path}>
                  <SidebarMenuButton
                    render={
                      <Link href={href} onClick={() => setOpenMobile(false)} />
                    }
                    isActive={pathname.startsWith(href)}
                    tooltip={label}
                    className={NAV_BUTTON}
                  >
                    <Icon />
                    <span>{label}</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter className="px-2.5 pb-2.5">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              render={
                <Link href="/sites" onClick={() => setOpenMobile(false)} />
              }
              isActive={pathname === "/sites"}
              tooltip="All sites"
              className={NAV_BUTTON}
            >
              <Globe />
              <span>All sites</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <div className="border-border mt-1.5 flex items-center gap-2.5 border-t pt-3 pr-1 pl-2 group-data-[collapsible=icon]:flex-col group-data-[collapsible=icon]:px-0">
          <span
            aria-hidden
            className="bg-muted text-foreground/70 flex size-[26px] shrink-0 items-center justify-center rounded-full text-[11px] font-semibold uppercase"
          >
            {email?.charAt(0) ?? "?"}
          </span>
          <span className="text-foreground/65 min-w-0 flex-1 truncate text-[12.5px] group-data-[collapsible=icon]:hidden">
            {email}
          </span>
          <button
            type="button"
            onClick={() => logout()}
            aria-label="Log out"
            title="Log out"
            className="text-foreground/65 hover:bg-muted hover:text-foreground focus-visible:ring-ring/50 flex size-7 shrink-0 items-center justify-center rounded-[7px] outline-none focus-visible:ring-3"
          >
            <LogOut className="size-[15px]" />
          </button>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
