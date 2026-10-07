import { describe, expect, it } from "vitest";

import { sanitizeNext } from "./next-url";

describe("sanitizeNext", () => {
  it("keeps a relative path", () => {
    expect(sanitizeNext("/sites/acme/articles/123")).toBe(
      "/sites/acme/articles/123",
    );
  });

  it("falls back to / for a protocol-relative URL", () => {
    expect(sanitizeNext("//evil.com")).toBe("/");
  });

  it("falls back to / for an absolute URL", () => {
    expect(sanitizeNext("https://evil.com")).toBe("/");
  });

  it("falls back to / when missing", () => {
    expect(sanitizeNext(null)).toBe("/");
    expect(sanitizeNext(undefined)).toBe("/");
  });
});
