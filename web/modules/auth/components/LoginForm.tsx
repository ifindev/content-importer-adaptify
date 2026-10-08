"use client";

import { signInWithEmailAndPassword, signOut } from "firebase/auth";
import { FirebaseError } from "firebase/app";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ArrowUpRight, CircleAlert, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { auth } from "@/lib/firebase-client";
import { sanitizeNext } from "@/modules/auth/lib/next-url";
import { createSession } from "@/modules/auth/repository/auth.mutations";

const FIREBASE_ERROR_MESSAGE: Record<string, string> = {
  "auth/invalid-credential": "Wrong email or password.",
  "auth/too-many-requests": "Too many attempts. Try again later.",
  "auth/network-request-failed": "Can't reach the server.",
};

export function LoginForm({
  next,
  sessionExpired,
}: {
  next: string | null;
  sessionExpired: boolean;
}) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    setSubmitting(true);
    setError(null);

    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");

    try {
      const credential = await signInWithEmailAndPassword(
        auth,
        email,
        password,
      );
      const idToken = await credential.user.getIdToken();
      await signOut(auth);

      const result = await createSession(idToken, credential.user.email);
      if (!result.ok) {
        setError("Sign-in failed. Try again.");
        setSubmitting(false);
        return;
      }

      router.push(sanitizeNext(next));
    } catch (err) {
      if (err instanceof FirebaseError) {
        setError(
          FIREBASE_ERROR_MESSAGE[err.code] ?? "Sign-in failed. Try again.",
        );
      } else {
        setError("Can't reach the server.");
      }
      setSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-[360px]">
      <div className="mb-6 flex flex-col items-center text-center">
        <span className="bg-foreground text-background mb-4 flex size-9 items-center justify-center rounded-[10px]">
          <ArrowUpRight className="size-[18px]" strokeWidth={2.5} />
        </span>
        <h1 className="text-xl font-semibold tracking-tight">
          Sign in to Content Importer
        </h1>
        <p className="text-muted-foreground mt-1 text-[13.5px]">
          {sessionExpired ? "Please sign in again." : "Use your agency account"}
        </p>
      </div>
      <form
        // onSubmit, not action: React resets a form after its action runs,
        // which would clear the email after a wrong password.
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit(new FormData(e.currentTarget));
        }}
        className="bg-card flex flex-col gap-4 rounded-xl border p-6 shadow-[0_1px_3px_oklch(0_0_0/0.05)]"
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            disabled={submitting}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            disabled={submitting}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "login-error" : undefined}
          />
          {error && (
            <p
              id="login-error"
              role="alert"
              className="text-destructive flex items-center gap-1.5 text-[12.5px]"
            >
              <CircleAlert className="size-3.5 shrink-0" />
              {error}
            </p>
          )}
        </div>
        <Button type="submit" disabled={submitting} className="mt-1 w-full">
          {submitting && <Loader2 className="animate-spin" />}
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
      {/* The public demo account exists only on the live app. */}
      {process.env.NODE_ENV === "production" && (
        <p className="text-muted-foreground mt-4 text-center text-[12.5px]">
          Demo login:{" "}
          <span className="text-foreground font-medium">
            agency@example.com
          </span>{" "}
          / <span className="text-foreground font-medium">pass@123</span>
        </p>
      )}
    </div>
  );
}
