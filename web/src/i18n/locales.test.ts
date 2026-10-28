import { describe, expect, it } from "vitest";

import { isLocale, negotiateLocale, splitLocale, withLocale } from "./locales";

describe("negotiateLocale", () => {
  it("picks the highest-weighted supported language", () => {
    expect(negotiateLocale("de-DE,ro;q=0.8,en;q=0.5")).toBe("ro");
    expect(negotiateLocale("en-GB,en;q=0.9,ro;q=0.8")).toBe("en");
    expect(negotiateLocale("ro;q=0.2,en;q=0.9")).toBe("en");
  });

  it("falls back to English", () => {
    expect(negotiateLocale(null)).toBe("en");
    expect(negotiateLocale("de,fr;q=0.5")).toBe("en");
    expect(negotiateLocale("ro;q=0")).toBe("en");
  });
});

describe("paths", () => {
  it("adds and removes the language prefix", () => {
    expect(withLocale("ro", "/projects/3")).toBe("/ro/projects/3");
    expect(withLocale("en", "/")).toBe("/en");
    expect(splitLocale("/ro/projects/3")).toEqual(["ro", "/projects/3"]);
    expect(splitLocale("/en")).toEqual(["en", "/"]);
    expect(splitLocale("/projects/3")).toEqual([null, "/projects/3"]);
  });

  it("accepts only supported languages", () => {
    expect(isLocale("ro")).toBe(true);
    expect(isLocale("favicon.ico")).toBe(false);
    expect(isLocale(undefined)).toBe(false);
  });
});
