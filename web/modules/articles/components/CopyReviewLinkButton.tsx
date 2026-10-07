"use client";

import { Link2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

export function CopyReviewLinkButton({ url }: { url: string }) {
  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      toast.success("Review link copied.");
    } catch {
      toast.error("Couldn't copy. The link is " + url);
    }
  }

  return (
    <Button
      variant="outline"
      onClick={copy}
      aria-label="Copy review link"
      className="max-md:size-11 max-md:border-0 max-md:shadow-none"
    >
      <Link2 />
      <span className="max-md:hidden">Copy review link</span>
    </Button>
  );
}
