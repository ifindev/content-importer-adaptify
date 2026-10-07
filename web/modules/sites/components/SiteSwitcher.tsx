"use client";

import { Check, ChevronsUpDown, Globe, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useSidebar } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

import { siteHost } from "../site-host";

import { SiteAvatar } from "./SiteAvatar";

type SwitcherSite = { id: string; wp_base_url: string; connection_ok: boolean };

export function SiteSwitcher({
  sites,
  currentId,
}: {
  sites: SwitcherSite[];
  currentId: string | undefined;
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const { setOpenMobile } = useSidebar();
  const current = sites.find((s) => s.id === currentId);
  const shown = sites.filter((s) =>
    siteHost(s.wp_base_url).includes(query.trim().toLowerCase()),
  );

  function close() {
    setOpen(false);
    setOpenMobile(false);
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        aria-label="Switch site"
        className="border-border bg-background hover:bg-muted aria-expanded:border-primary/45 aria-expanded:ring-primary/12 flex h-9 w-full items-center gap-2 rounded-lg border px-2 text-[13px] font-medium shadow-xs outline-none group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:p-0 focus-visible:ring-3 aria-expanded:ring-3"
      >
        <SiteAvatar label={current ? siteHost(current.wp_base_url) : "?"} />
        <span className="min-w-0 flex-1 truncate text-left group-data-[collapsible=icon]:hidden">
          {current ? siteHost(current.wp_base_url) : "Choose a site"}
        </span>
        <ChevronsUpDown className="text-faint size-3.5 group-data-[collapsible=icon]:hidden" />
      </PopoverTrigger>
      <PopoverContent align="start" className="w-66 gap-0 p-1.5">
        <label className="relative block px-0.5 pt-0.5 pb-1.5">
          <Search className="text-faint pointer-events-none absolute top-[9px] left-2.5 size-3.5" />
          <input
            type="search"
            aria-label="Find a site"
            placeholder="Find a site"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="border-border focus-visible:border-primary/50 focus-visible:ring-primary/12 h-[30px] w-full rounded-md border pr-2.5 pl-[30px] text-[13px] outline-none focus-visible:ring-3"
          />
        </label>
        <div className="text-muted-foreground px-2 pt-1.5 pb-1 text-[11.5px] font-medium">
          Sites
        </div>
        <ul className="max-h-72 overflow-y-auto">
          {shown.map((site) => (
            <li key={site.id}>
              <Link
                href={`/sites/${site.id}/articles`}
                onClick={close}
                aria-current={site.id === currentId ? "page" : undefined}
                className={cn(
                  "hover:bg-muted focus-visible:bg-muted flex h-[34px] items-center gap-2 rounded-md px-2 text-[13px] outline-none",
                  site.id === currentId && "bg-muted",
                )}
              >
                <SiteAvatar label={siteHost(site.wp_base_url)} />
                <span className="min-w-0 flex-1 truncate">
                  {siteHost(site.wp_base_url)}
                </span>
                {!site.connection_ok && (
                  <span
                    title="Can't connect to WordPress"
                    className="size-[7px] shrink-0 rounded-full bg-red-600"
                  >
                    <span className="sr-only">
                      Can&apos;t connect to WordPress
                    </span>
                  </span>
                )}
                {site.id === currentId && <Check className="size-3.5" />}
              </Link>
            </li>
          ))}
          {shown.length === 0 && (
            <li className="text-muted-foreground px-2 py-2 text-[13px]">
              No sites match.
            </li>
          )}
        </ul>
        <div className="bg-border -mx-1.5 my-1.5 h-px" />
        <Link
          href="/sites"
          onClick={close}
          className="hover:bg-muted focus-visible:bg-muted text-foreground/80 flex h-[34px] items-center gap-2 rounded-md px-2 text-[13px] outline-none"
        >
          <Globe className="size-3.5" /> All sites
        </Link>
        <Link
          href="/sites?add=1"
          onClick={close}
          className="hover:bg-muted focus-visible:bg-muted text-foreground/80 flex h-[34px] items-center gap-2 rounded-md px-2 text-[13px] outline-none"
        >
          <Plus className="size-3.5" /> Add site
        </Link>
      </PopoverContent>
    </Popover>
  );
}
