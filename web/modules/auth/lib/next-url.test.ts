import { describe, expect, it } from "vitest";

import { sanitizeNext } from "./next-url";

describe("sanitizeNext", () => {
  it("keeps a relative path", () => {
    expect(sanitizeNext("/articles/123")).toBe("/articles/123");
  });

  it("falls back to /articles for a protocol-relative URL", () => {
    expect(sanitizeNext("//evil.com")).toBe("/articles");
  });

  it("falls back to /articles for an absolute URL", () => {
    expect(sanitizeNext("https://evil.com")).toBe("/articles");
  });

  it("falls back to /articles when missing", () => {
    expect(sanitizeNext(null)).toBe("/articles");
    expect(sanitizeNext(undefined)).toBe("/articles");
  });
});
