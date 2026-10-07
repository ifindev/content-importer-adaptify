import "server-only";

import { cookies } from "next/headers";

import type { MutationResult } from "@/lib/mutation-result";

/**
 * Fixture-only (T-033). Playwright and manual checks pick a screen state with
 * the `fixture_scenario` cookie: `wordpress-down`, `slow`, `empty`,
 * `no-sites`, `one-site`, `rate-limited`, or `error:<code>` to make every
 * mutation fail with that code. Deleted with the fixtures during wiring.
 */
export async function scenario(): Promise<string> {
  return (await cookies()).get("fixture_scenario")?.value ?? "";
}

export const delay = (ms = 400) =>
  new Promise((resolve) => setTimeout(resolve, ms));

/** Reads wait longer under `slow`, so loading skeletons are visible. */
export async function readDelay() {
  await delay((await scenario()) === "slow" ? 2000 : 0);
}

/** Every mutation calls this first: a short delay, then the scenario's error. */
export async function mutationFailure(): Promise<MutationResult<never> | null> {
  const current = await scenario();
  await delay(current === "slow" ? 2000 : 400);
  return current.startsWith("error:")
    ? { ok: false, code: current.slice("error:".length) }
    : null;
}
