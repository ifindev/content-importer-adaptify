"use client";

import { signInWithEmailAndPassword, signOut } from "firebase/auth";
import { FirebaseError } from "firebase/app";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { auth } from "@/lib/firebase-client";
import { sanitizeNext } from "@/modules/auth/lib/next-url";
import { createSession } from "@/modules/auth/repository/auth.mutations";

const FIREBASE_ERROR_MESSAGE: Record<string, string> = {
  "auth/invalid-credential": "Wrong email or password.",
  "auth/too-many-requests": "Too many attempts. Try again later.",
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
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>Sign in</CardTitle>
        {sessionExpired && (
          <CardDescription>Please sign in again.</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        <form action={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
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
          <div className="flex flex-col gap-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              disabled={submitting}
            />
          </div>
          {error && <p className="text-destructive text-sm">{error}</p>}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
