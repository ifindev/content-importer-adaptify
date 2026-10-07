"use client";

import { Button } from "@/components/ui/button";

export default function Error({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="flex flex-col items-start gap-3 p-4">
      <p className="text-sm">Something went wrong.</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
