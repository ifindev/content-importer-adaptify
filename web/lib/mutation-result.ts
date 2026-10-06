export type MutationResult<T> =
  { ok: true; data: T } | { ok: false; code: string };
