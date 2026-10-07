import { cookies } from "next/headers";
import { Toaster } from "sonner";

import { AgencySidebarProvider } from "@/components/agency-sidebar-provider";
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";

export default async function AgencyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const cookieStore = await cookies();
  const defaultOpen = cookieStore.get("sidebar_state")?.value !== "false";
  const email = cookieStore.get("agency_email")?.value ?? null;

  return (
    <AgencySidebarProvider defaultOpen={defaultOpen}>
      <AppSidebar email={email} />
      <SidebarInset>
        <header className="flex h-14 items-center gap-2 border-b px-4 md:hidden">
          <SidebarTrigger />
        </header>
        <main className="flex-1 p-4">{children}</main>
      </SidebarInset>
      <Toaster />
    </AgencySidebarProvider>
  );
}
