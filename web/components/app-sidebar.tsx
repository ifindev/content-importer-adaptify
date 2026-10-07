"use client";

import { FileText, Import, LogOut, Newspaper } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { logout } from "@/modules/auth/repository/auth.mutations";

const NAV_ITEMS = [
  { href: "/import", label: "Import", icon: Import },
  { href: "/articles", label: "Articles", icon: FileText },
  { href: "/report", label: "Report", icon: Newspaper },
];

export function AppSidebar({ email }: { email: string | null }) {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="truncate p-4 text-sm font-semibold group-data-[collapsible=icon]:hidden">
        Content Importer
      </SidebarHeader>
      <SidebarContent>
        <SidebarMenu>
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
            <SidebarMenuItem key={href}>
              <SidebarMenuButton
                render={<Link href={href} />}
                isActive={pathname.startsWith(href)}
                tooltip={label}
              >
                <Icon />
                <span>{label}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          {email && (
            <SidebarMenuItem>
              <span className="text-muted-foreground block truncate px-2 py-1 text-xs group-data-[collapsible=icon]:hidden">
                {email}
              </span>
            </SidebarMenuItem>
          )}
          <SidebarMenuItem>
            <SidebarMenuButton
              render={<button type="button" onClick={() => logout()} />}
              tooltip="Logout"
            >
              <LogOut />
              <span>Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
