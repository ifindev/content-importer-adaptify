import { SidebarTrigger } from "@/components/ui/sidebar";
import { ImportForm } from "@/modules/articles/components/ImportForm";

export function ImportPage({ siteId }: { siteId: string }) {
  return (
    <div className="mx-auto flex w-full max-w-[760px] flex-col gap-5 px-4 pt-2 pb-8 md:px-7 md:pt-[22px]">
      <header className="flex items-center gap-1">
        <SidebarTrigger
          className="-ml-3 size-11 md:hidden"
          aria-label="Open menu"
        />
        <div>
          <h1 className="text-xl leading-tight font-semibold tracking-tight">
            Import
          </h1>
          <p className="text-muted-foreground mt-0.5 text-[13px]">
            Paste an article, or upload one or more .docx files.
          </p>
        </div>
      </header>
      <ImportForm siteId={siteId} />
    </div>
  );
}
