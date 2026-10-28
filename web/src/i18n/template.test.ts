import { describe, expect, it } from "vitest";

import { fill, plural } from "./template";

describe("fill", () => {
  it("replaces known placeholders and keeps unknown ones visible", () => {
    expect(fill("Page {page} of {total}", { page: 2 })).toBe(
      "Page 2 of {total}",
    );
  });
});

describe("plural", () => {
  const ro = {
    one: "{count} pagină",
    few: "{count} pagini",
    other: "{count} de pagini",
  };

  it("uses Romanian's three forms", () => {
    expect(plural("ro", 1, ro)).toBe("1 pagină");
    expect(plural("ro", 3, ro)).toBe("3 pagini");
    expect(plural("ro", 25, ro)).toBe("25 de pagini");
  });

  it("uses English's two forms", () => {
    const en = { one: "{count} page", other: "{count} pages" };
    expect(plural("en", 1, en)).toBe("1 page");
    expect(plural("en", 0, en)).toBe("0 pages");
  });
});
