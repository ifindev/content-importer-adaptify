import { TriangleAlert } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";

export function WordPressBanner() {
  return (
    <Alert variant="destructive">
      <TriangleAlert />
      <AlertDescription>
        Can&apos;t reach WordPress. Statuses may be out of date.
      </AlertDescription>
    </Alert>
  );
}
