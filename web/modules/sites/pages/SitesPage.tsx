import { Check, Globe, Plus } from "lucide-react";
import { cookies } from "next/headers";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { SiteDialog } from "@/modules/sites/components/SiteDialog";
import { SiteRowActions } from "@/modules/sites/components/SiteRowActions";
import { SiteAvatar } from "@/modules/sites/components/SiteAvatar";
import { siteHost } from "@/modules/sites/site-host";
import { TestConnectionButton } from "@/modules/sites/components/TestConnectionButton";
import { LAST_SITE_COOKIE } from "@/lib/last-site";
import { listSites, type SiteWithStats } from "@/modules/sites/data";

export async function SitesPage() {
  const [{ sites }, cookieStore] = await Promise.all([listSites(), cookies()]);
  const currentId = cookieStore.get(LAST_SITE_COOKIE)?.value;

  return (
    <>
      {sites.length === 0 ? (
        <ZeroSites />
      ) : (
        <SitesList sites={sites} currentId={currentId} />
      )}
      <SiteDialog sites={sites} allowHttp={process.env.APP_ENV === "local"} />
    </>
  );
}

function AddSiteLink() {
  return (
    <Link href="/sites?add=1" className={buttonVariants()}>
      <Plus /> Add site
    </Link>
  );
}

function SitesList({
  sites,
  currentId,
}: {
  sites: SiteWithStats[];
  currentId: string | undefined;
}) {
  return (
    <>
      <PageHeader
        title="Sites"
        subtitle={`${sites.length} client ${sites.length === 1 ? "site" : "sites"}`}
      >
        <AddSiteLink />
      </PageHeader>
      <div className="md:px-4 md:pt-[18px] md:pb-5">
        <table className="w-full border-collapse text-[13px]">
          <thead className="max-md:sr-only">
            <tr className="text-muted-foreground border-b text-left text-xs">
              <th className="h-9 px-3 font-medium">Site</th>
              <th className="h-9 w-[190px] px-3 font-medium">WordPress</th>
              <th className="h-9 w-[110px] px-3 text-right font-medium">
                Articles
              </th>
              <th className="h-9 w-[140px] px-3 text-right font-medium">
                Needs attention
              </th>
              <th className="h-9 w-[190px] px-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {sites.map((site) => (
              <tr
                key={site.id}
                className="hover:bg-muted/40 border-b border-[oklch(0.955_0.003_264)] max-md:flex max-md:flex-wrap max-md:items-center max-md:gap-x-3 max-md:px-4 max-md:py-3.5"
              >
                <td className="px-3 py-2 max-md:w-full max-md:p-0 md:h-[60px]">
                  <Link
                    href={`/sites/${site.id}/articles`}
                    className="focus-visible:ring-ring/50 flex items-center gap-3 rounded-md outline-none focus-visible:ring-3"
                  >
                    <SiteAvatar label={site.name} size="lg" />
                    <span className="min-w-0">
                      <span className="flex items-center gap-2 text-[13.5px] font-medium">
                        {site.name}
                        {site.id === currentId && (
                          <Badge variant="outline">Current</Badge>
                        )}
                      </span>
                      <span className="text-muted-foreground block truncate text-[12.5px]">
                        {siteHost(site.wp_base_url)}
                      </span>
                    </span>
                  </Link>
                </td>
                <td className="px-3 py-2 max-md:p-0 max-md:pl-11">
                  <ConnectionStatus site={site} />
                </td>
                <td className="text-foreground/70 px-3 py-2 text-right tabular-nums max-md:p-0 max-md:text-[12.5px]">
                  <span className="md:hidden">· </span>
                  {site.article_count}
                  <span className="md:hidden"> articles</span>
                </td>
                <td className="text-foreground/70 px-3 py-2 text-right tabular-nums max-md:hidden">
                  {site.needs_attention_count || (
                    <span className="text-faint">—</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right max-md:ml-auto max-md:p-0">
                  <div className="flex items-center justify-end gap-1">
                    {!site.connection_ok && (
                      <TestConnectionButton site={site} />
                    )}
                    <SiteRowActions site={site} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function ConnectionStatus({ site }: { site: SiteWithStats }) {
  if (site.connection_ok) {
    return (
      <span className="text-foreground/70 inline-flex items-center gap-[7px]">
        <span className="size-[7px] rounded-full bg-emerald-600" />
        Connected
      </span>
    );
  }
  return (
    <>
      <span className="text-status-failed-fg inline-flex items-center gap-[7px]">
        <span className="size-[7px] rounded-full bg-red-600" />
        Can&apos;t connect
      </span>
      {site.connection_checked_at && (
        <span className="text-muted-foreground block pl-3.5 text-xs max-md:hidden">
          Last checked{" "}
          {new Date(site.connection_checked_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          })}
        </span>
      )}
    </>
  );
}

function ZeroSites() {
  return (
    <>
      <SidebarTrigger
        className="m-1 size-11 md:hidden"
        aria-label="Open menu"
      />
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="flex max-w-[400px] flex-col items-center text-center">
          <span className="bg-background mb-[18px] flex size-12 items-center justify-center rounded-xl border shadow-xs">
            <Globe className="text-foreground/70 size-[22px]" />
          </span>
          <h1 className="text-lg font-semibold tracking-tight">
            Add your first client site
          </h1>
          <p className="text-muted-foreground mt-1.5 text-[13.5px] leading-relaxed">
            Connect a client&apos;s WordPress site to start importing articles,
            collecting approvals, and scheduling posts.
          </p>
          <div className="my-6 flex flex-col gap-2.5 self-stretch rounded-[10px] border border-[oklch(0.95_0.003_264)] bg-[oklch(0.985_0_0)] px-4 py-3.5 text-left">
            <span className="text-muted-foreground text-xs font-medium">
              You&apos;ll need
            </span>
            {[
              "The site's URL",
              "A WordPress username",
              "An application password for that user",
            ].map((need) => (
              <span key={need} className="flex items-center gap-2 text-[13px]">
                <Check className="text-faint size-3.5" />
                {need}
              </span>
            ))}
          </div>
          <AddSiteLink />
        </div>
      </div>
    </>
  );
}
