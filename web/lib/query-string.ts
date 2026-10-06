export function mergeQueryString(
  current: URLSearchParams,
  patch: Record<string, string | undefined>,
): string {
  const params = new URLSearchParams(current);
  for (const [key, value] of Object.entries(patch)) {
    if (value === undefined) {
      params.delete(key);
    } else {
      params.set(key, value);
    }
  }
  return params.toString();
}
