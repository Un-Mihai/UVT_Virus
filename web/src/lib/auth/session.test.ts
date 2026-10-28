import { expect, it } from "vitest";

import { safeReturnTo, seal, unseal } from "./session";

it("round-trips sealed values and rejects anything else", async () => {
  const sealed = await seal({ refreshToken: "secret" }, 60);

  expect(sealed).not.toContain("secret");
  expect(await unseal(sealed)).toEqual({ refreshToken: "secret" });
  expect(await unseal(sealed.slice(0, -2) + "xx")).toBeNull();
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
