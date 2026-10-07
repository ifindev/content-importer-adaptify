"use client";

import { useEffect, useState } from "react";

import { SidebarProvider } from "@/components/ui/sidebar";

const SIDEBAR_COOKIE_NAME = "sidebar_state";
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;

/**
 * Wraps shadcn's SidebarProvider to add the ticket's third breakpoint: an
 * icon rail by default between md (768px) and lg (1024px) that ignores the
 * user's lg+ expand/collapse preference, which is cookie-persisted as usual.
 */
export function AgencySidebarProvider({
  defaultOpen,
  children,
}: {
  defaultOpen: boolean;
  children: React.ReactNode;
}) {
  const [userOpen, setUserOpen] = useState(defaultOpen);
  const [isRail, setIsRail] = useState(false);

  useEffect(() => {
    const rail = window.matchMedia(
      "(min-width: 768px) and (max-width: 1023.98px)",
    );
    const apply = () => setIsRail(rail.matches);
    apply();
    rail.addEventListener("change", apply);
    return () => rail.removeEventListener("change", apply);
  }, []);

  return (
    <SidebarProvider
      open={isRail ? false : userOpen}
      onOpenChange={(open) => {
        setUserOpen(open);
        document.cookie = `${SIDEBAR_COOKIE_NAME}=${open}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
      }}
    >
      {children}
    </SidebarProvider>
  );
}
