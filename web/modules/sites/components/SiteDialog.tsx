"use client";

import {
  CircleAlert,
  CircleCheck,
  Eye,
  EyeOff,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useRef, useState, useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { messageFor } from "@/lib/error-messages";
import {
  createSite,
  testConnection,
  updateSite,
} from "@/modules/sites/actions";

type TestState = "idle" | "pending" | "passed" | "failed";

type EditableSite = {
  id: string;
  name: string;
  wp_base_url: string;
  wp_username: string;
};

/**
 * Add (`?add=1`, so the switcher's "Add site" can link straight to it) or
 * edit (`?edit=<siteId>`) a client site. `allowHttp` (APP_ENV=local only)
 * accepts http:// URLs such as the local WordPress container.
 */
export function SiteDialog({
  sites,
  allowHttp = false,
}: {
  sites: EditableSite[];
  allowHttp?: boolean;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const editing = sites.find((s) => s.id === params.get("edit"));
  const open = params.get("add") === "1" || editing !== undefined;
  const formRef = useRef<HTMLFormElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [test, setTest] = useState<TestState>("idle");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, startSubmit] = useTransition();
  const [, startTest] = useTransition();

  function close() {
    setError(null);
    setTest("idle");
    // Client-only URL update: Next syncs it into useSearchParams without a
    // server round trip, so the dialog closes at once.
    window.history.replaceState(null, "", pathname);
  }

  function fields() {
    const data = new FormData(formRef.current!);
    return {
      name: String(data.get("name") ?? "").trim(),
      wp_base_url: String(data.get("wp_base_url") ?? "").trim(),
      wp_username: String(data.get("wp_username") ?? "").trim(),
      wp_app_password: String(data.get("wp_app_password") ?? ""),
    };
  }

  function submit() {
    setError(null);
    startSubmit(async () => {
      if (editing) {
        const values = fields();
        // Send only what changed; an empty password keeps the stored one.
        const result = await updateSite(editing.id, {
          name: values.name !== editing.name ? values.name : undefined,
          wp_base_url:
            values.wp_base_url !== editing.wp_base_url
              ? values.wp_base_url
              : undefined,
          wp_username:
            values.wp_username !== editing.wp_username
              ? values.wp_username
              : undefined,
          wp_app_password: values.wp_app_password || undefined,
        });
        if (!result.ok) {
          setError(result.code);
          return;
        }
        toast.success(`${result.data.name} saved.`);
        close();
        return;
      }
      const result = await createSite(fields());
      if (!result.ok) {
        setError(result.code);
        return;
      }
      toast.success(`${result.data.name} added.`);
      router.push(`/sites/${result.data.id}/articles`);
    });
  }

  function runTest() {
    if (!formRef.current?.reportValidity()) return;
    setError(null);
    setTest("pending");
    startTest(async () => {
      const { wp_base_url, wp_username, wp_app_password } = fields();
      // Editing tests against the stored site, so an empty password means
      // the stored one.
      const result = await testConnection(
        { wp_base_url, wp_username, wp_app_password },
        editing?.id,
      );
      setTest(result.ok ? "passed" : "failed");
    });
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && close()}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] gap-0 overflow-y-auto rounded-[14px] p-0 sm:max-w-[480px]">
        <div className="px-6 pt-5 pr-12">
          <DialogTitle className="text-[17px] font-semibold tracking-tight">
            {editing ? `Edit ${editing.name}` : "Add a client site"}
          </DialogTitle>
          <DialogDescription className="text-muted-foreground mt-1 text-[13.5px]">
            {editing
              ? "Changed WordPress details are checked before saving."
              : "We check the WordPress connection before saving."}
          </DialogDescription>
        </div>
        <form
          ref={formRef}
          id="site-form"
          // New defaults when switching between sites.
          key={editing?.id ?? "add"}
          action={submit}
          onChange={() => {
            // Editing a field makes the last result stale.
            setError(null);
            if (test !== "pending") setTest("idle");
          }}
          className="flex flex-col gap-4 px-6 pt-5 pb-[22px]"
        >
          {error && (
            <div
              role="alert"
              className="flex gap-2.5 rounded-[9px] border border-[oklch(0.91_0.045_27.325)] bg-[oklch(0.97_0.015_27.325)] px-3 py-2.5 text-[13px] leading-snug text-[oklch(0.42_0.17_27.325)]"
            >
              <CircleAlert className="mt-px size-4 shrink-0" />
              {messageFor(error)}
            </div>
          )}
          <Field label="Site name" id="name">
            <Input
              id="name"
              name="name"
              defaultValue={editing?.name}
              required
              disabled={submitting}
            />
          </Field>
          <Field
            label="WordPress URL"
            id="wp_base_url"
            hint={
              allowHttp
                ? "The site's home address. http:// is allowed locally, e.g. http://wordpress."
                : "The site's home address, starting with https://"
            }
          >
            <Input
              id="wp_base_url"
              name="wp_base_url"
              type="url"
              pattern={allowHttp ? "https?://.*" : "https://.*"}
              placeholder="https://"
              defaultValue={editing?.wp_base_url}
              required
              disabled={submitting}
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2 sm:gap-3">
            <Field label="WordPress username" id="wp_username">
              <Input
                id="wp_username"
                name="wp_username"
                autoComplete="off"
                defaultValue={editing?.wp_username}
                required
                disabled={submitting}
              />
            </Field>
            <Field label="Application password" id="wp_app_password">
              <div className="relative">
                <Input
                  id="wp_app_password"
                  name="wp_app_password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="off"
                  placeholder={editing ? "Unchanged" : undefined}
                  required={!editing}
                  disabled={submitting}
                  className="pr-9"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute top-0.5 right-0.5"
                >
                  {showPassword ? <EyeOff /> : <Eye />}
                </Button>
              </div>
            </Field>
          </div>
          <span className="text-muted-foreground -mt-2 text-xs">
            {editing && "Leave the password empty to keep the current one. "}
            Create one in WordPress under Users → Profile → Application
            Passwords.
          </span>
        </form>
        <div className="flex flex-wrap items-center gap-2 rounded-b-[14px] border-t bg-[oklch(0.985_0_0)] px-6 py-3.5">
          <Button
            type="button"
            variant="outline"
            onClick={runTest}
            disabled={test === "pending" || submitting}
          >
            {test === "pending" ? (
              <Loader2 className="animate-spin" />
            ) : (
              <RefreshCw />
            )}
            Test connection
          </Button>
          <span role="status" className="text-[12.5px]">
            {test === "passed" && (
              <span className="text-status-approved-fg inline-flex items-center gap-1">
                <CircleCheck className="size-3.5" /> Connected
              </span>
            )}
            {test === "failed" && (
              <span className="text-status-failed-fg inline-flex items-center gap-1">
                <CircleAlert className="size-3.5" /> Can&apos;t connect
              </span>
            )}
          </span>
          <div className="flex-1" />
          <DialogClose render={<Button variant="ghost" />}>Cancel</DialogClose>
          <Button type="submit" form="site-form" disabled={submitting}>
            {submitting && <Loader2 className="animate-spin" />}
            {editing ? "Save" : "Add site"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  label,
  id,
  hint,
  children,
}: {
  label: string;
  id: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <span className="text-muted-foreground text-xs">{hint}</span>}
    </div>
  );
}
