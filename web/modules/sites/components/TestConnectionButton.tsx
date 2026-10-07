"use client";

import { Loader2, RefreshCw } from "lucide-react";
import { useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { messageFor } from "@/lib/error-messages";
import { testConnection } from "@/modules/sites/actions";

export function TestConnectionButton({
  site,
}: {
  site: { name: string; wp_base_url: string };
}) {
  const [pending, startTransition] = useTransition();

  return (
    <Button
      variant="outline"
      size="sm"
      disabled={pending}
      onClick={() =>
        startTransition(async () => {
          // ponytail: fixture-only; the real endpoint needs the stored creds.
          const result = await testConnection({
            wp_base_url: site.wp_base_url,
            wp_username: "",
            wp_app_password: "",
          });
          if (result.ok) toast.success(`Connected to ${site.name}.`);
          else toast.error(messageFor(result.code));
        })
      }
    >
      {pending ? <Loader2 className="animate-spin" /> : <RefreshCw />}
      Test connection
    </Button>
  );
}
