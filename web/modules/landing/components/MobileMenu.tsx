"use client";

import { Menu } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { DARK_BUTTON, LINKS, NAV } from "@/modules/landing/content";

export function MobileMenu() {
  const [open, setOpen] = useState(false);
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button
            variant="ghost"
            size="icon"
            className="-mr-2.5 ml-auto size-11 md:hidden"
            aria-label="Menu"
            title="Menu"
          />
        }
      >
        <Menu className="size-5" />
      </SheetTrigger>
      <SheetContent side="right" className="gap-0 p-5 pt-14">
        <SheetTitle className="sr-only">Menu</SheetTitle>
        <nav aria-label="Sections" className="flex flex-col">
          {NAV.map((item) => (
            <a
              key={item.href}
              href={item.href}
              onClick={() => setOpen(false)}
              className="border-b py-3.5 text-[17px] font-medium"
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="mt-6 flex flex-col gap-2.5">
          <Link
            href={LINKS.demo}
            className={cn(buttonVariants(), "h-11 text-[15px]", DARK_BUTTON)}
          >
            Try the demo
          </Link>
          <Link
            href={LINKS.signIn}
            className={cn(
              buttonVariants({ variant: "outline" }),
              "h-11 text-[15px]",
            )}
          >
            Sign in
          </Link>
        </div>
      </SheetContent>
    </Sheet>
  );
}
