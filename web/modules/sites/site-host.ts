/** "https://acme-running.com" → "acme-running.com". */
export const siteHost = (url: string) => url.replace(/^https?:\/\//, "");
