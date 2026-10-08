import Link from "next/link";

import { LogoMark } from "@/components/logo";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { DARK_BUTTON, LINKS, NAV } from "@/modules/landing/content";
import { MobileMenu } from "@/modules/landing/components/MobileMenu";

export function Wordmark() {
  return (
    <Link href="/" className="flex items-center gap-2.5">
      <LogoMark size="md" />
      <span className="display text-[17px] font-semibold md:text-lg">
        Content Importer
      </span>
    </Link>
  );
}

export function LandingHeader() {
  return (
    <header className="landing-header sticky top-0 z-40">
      <div className="mx-auto flex h-15 max-w-[1180px] items-center gap-10 px-5 md:h-[72px] md:px-12">
        <Wordmark />
        <nav aria-label="Sections" className="hidden gap-7 text-[15px] md:flex">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="hover:text-muted-foreground transition-colors"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="ml-auto hidden gap-2 md:flex">
          <Link
            href={LINKS.signIn}
            className={cn(
              buttonVariants({ variant: "outline" }),
              "h-[34px] px-3.5 text-[13.5px]",
            )}
          >
            Sign in
          </Link>
          <Link
            href={LINKS.demo}
            className={cn(
              buttonVariants(),
              "h-[34px] px-3.5 text-[13.5px]",
              DARK_BUTTON,
            )}
          >
            Try the demo
          </Link>
        </div>
        <MobileMenu />
      </div>
    </header>
  );
}
