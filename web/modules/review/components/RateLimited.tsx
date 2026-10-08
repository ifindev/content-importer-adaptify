import { CircleAlert } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";

/** The review API allows a few requests per minute per client (spec R8.2). */
export function RateLimited({ href }: { href: string }) {
  return (
    <div
      role="alert"
      className="bg-app flex min-h-svh items-center justify-center p-6 text-center"
    >
      <div className="max-w-sm">
        <CircleAlert className="text-faint mx-auto mb-3 size-6" />
        <h1 className="text-[15px] font-semibold">Too many requests</h1>
        <p className="text-muted-foreground mt-1 text-[13.5px]">
          Wait a minute, then try again.
        </p>
        <a
          href={href}
          className={buttonVariants({ variant: "outline", className: "mt-4" })}
        >
          Try again
        </a>
      </div>
    </div>
  );
}
