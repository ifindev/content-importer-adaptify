"use client";

import { CircleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="bg-app flex min-h-svh items-center justify-center p-6 text-center">
      <div className="max-w-sm">
        <CircleAlert className="text-faint mx-auto mb-3 size-6" />
        <h1 className="text-[15px] font-semibold">Something went wrong</h1>
        <p className="text-muted-foreground mt-1 text-[13.5px]">
          Try again in a moment.
        </p>
        <Button variant="outline" className="mt-4" onClick={reset}>
          Try again
        </Button>
      </div>
    </div>
  );
}
