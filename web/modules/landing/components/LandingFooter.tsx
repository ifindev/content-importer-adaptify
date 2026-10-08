import Link from "next/link";

import { LINKS } from "@/modules/landing/content";

export function LandingFooter() {
  return (
    <footer className="border-t">
      <div className="text-muted-foreground mx-auto flex max-w-[1180px] flex-col-reverse gap-3 px-5 py-6 text-[13px] md:h-[72px] md:flex-row md:items-center md:justify-between md:px-12 md:py-0 md:text-[13.5px]">
        <p>
          © 2026 Content Importer · An independent project, not affiliated with
          Adaptify SEO.
        </p>
        <nav
          aria-label="Footer"
          className="text-foreground md:text-muted-foreground flex gap-6 font-medium md:font-normal"
        >
          <a href={LINKS.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={LINKS.apiDocs} target="_blank" rel="noreferrer">
            API docs
          </a>
          <Link href={LINKS.signIn}>Sign in</Link>
        </nav>
      </div>
    </footer>
  );
}
