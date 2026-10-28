import { expect, it } from "vitest";

import { safeReturnTo, seal, unseal } from "./session";

it("round-trips sealed values and rejects anything else", async () => {
  const sealed = await seal({ refreshToken: "secret" }, 60);

  expect(sealed).not.toContain("secret");
  expect(await unseal(sealed)).toEqual({ refreshToken: "secret" });
  // Change a ciphertext character: the last ones can be padding bits that decode the same.
  const [header, key, iv, ciphertext, tag] = sealed.split(".");
  const flipped = (ciphertext[0] === "A" ? "B" : "A") + ciphertext.slice(1);
  expect(await unseal([header, key, iv, flipped, tag].join("."))).toBeNull();
  expect(await unseal(undefined)).toBeNull();
});

it("only returns to paths on this site", () => {
  expect(safeReturnTo("/status?x=1")).toBe("/status?x=1");
  expect(safeReturnTo("//evil.example")).toBe("/");
  expect(safeReturnTo("/\\evil.example")).toBe("/");
  expect(safeReturnTo("https://evil.example")).toBe("/");
  expect(safeReturnTo("http://[")).toBe("/");
  expect(safeReturnTo(null)).toBe("/");
});
