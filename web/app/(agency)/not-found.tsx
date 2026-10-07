import { FileQuestion } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <FileQuestion className="text-faint mb-3 size-6" />
      <h1 className="text-[15px] font-semibold">Not found</h1>
      <p className="text-muted-foreground mt-1 text-[13.5px]">
        This page doesn&apos;t exist, or the article or site was removed.
      </p>
      <Link
        href="/sites"
        className={buttonVariants({ variant: "outline", className: "mt-4" })}
      >
        All sites
      </Link>
    </div>
  );
}
