import { describe, expect, it } from "vitest";

import { sanitizeNext } from "./next-url";

describe("sanitizeNext", () => {
  it("keeps a relative path", () => {
    expect(sanitizeNext("/sites/acme/articles/123")).toBe(
      "/sites/acme/articles/123",
    );
  });

  it("falls back to /app for a protocol-relative URL", () => {
    expect(sanitizeNext("//evil.com")).toBe("/app");
  });

  it("falls back to /app for an absolute URL", () => {
    expect(sanitizeNext("https://evil.com")).toBe("/app");
  });

  it("falls back to /app when missing", () => {
    expect(sanitizeNext(null)).toBe("/app");
    expect(sanitizeNext(undefined)).toBe("/app");
  });
});
