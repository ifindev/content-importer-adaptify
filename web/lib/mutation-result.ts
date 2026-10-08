import { ApiError } from "@/lib/http";

export type MutationResult<T> =
  { ok: true; data: T } | { ok: false; code: string };

/**
 * Turns an API call into a MutationResult. A 4xx carries a `code` the UI
 * shows with `messageFor`; anything else (5xx, network) is thrown so the
 * route's error.tsx shows it.
 */
export async function toResult<T>(call: Promise<T>): Promise<MutationResult<T>> {
  try {
    return { ok: true, data: await call };
  } catch (error) {
    if (error instanceof ApiError && error.status < 500)
      return { ok: false, code: error.code };
    throw error;
  }
}

/** Runs a read; a 404 becomes Next's notFound() via `onNotFound`. */
export async function orNotFound<T>(
  call: Promise<T>,
  onNotFound: () => never,
): Promise<T> {
  try {
    return await call;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) onNotFound();
    throw error;
  }
}
