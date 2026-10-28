import { expect, it } from "vitest";

import { en } from "./en";
import { ro } from "./ro";

/** Every leaf as "path → value", so missing or empty translations show by name. */
function leaves(node: object, path = ""): [string, unknown][] {
  return Object.entries(node).flatMap(([key, value]) =>
    value !== null && typeof value === "object"
      ? leaves(value, `${path}${key}.`)
      : [[`${path}${key}`, value]],
  );
}

it("translates every string, with the same placeholders", () => {
  const romanian = new Map(leaves(ro));
  for (const [path, english] of leaves(en)) {
    const translated = romanian.get(path);
    expect(translated, path).toBeTypeOf("string");
    expect(translated, path).not.toBe("");
    const placeholders = (text: unknown) =>
      [...String(text).matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort();
    expect(placeholders(translated), path).toEqual(placeholders(english));
  }
});
