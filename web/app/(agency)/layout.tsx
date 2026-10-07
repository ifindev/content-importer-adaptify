import { cookies } from "next/headers";
import { Toaster } from "sonner";

import { AgencySidebarProvider } from "@/components/agency-sidebar-provider";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarInset } from "@/components/ui/sidebar";
import { listSites } from "@/modules/sites/data";

export default async function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const defaultOpen = cookieStore.get("sidebar_state")?.value !== "false";
  const email = cookieStore.get("agency_email")?.value ?? null;
  const { sites } = await listSites();

  return (
    <AgencySidebarProvider defaultOpen={defaultOpen}>
      <AppSidebar email={email} sites={sites} />
      <SidebarInset className="bg-background min-w-0 md:peer-data-[variant=inset]:border md:peer-data-[variant=inset]:shadow-[0_1px_3px_oklch(0_0_0/0.04)]">
        {children}
      </SidebarInset>
      <Toaster />
    </AgencySidebarProvider>
  );
}
