import { describe, expect, it } from "vitest";

import { en } from "@/i18n/dictionaries/en";
import { ro } from "@/i18n/dictionaries/ro";

import { problemText } from "./problem";

const conflict = {
  status: 409,
  error: { detail: "Upload at least one document before submitting." },
};

describe("problemText", () => {
  it("shows the API's own sentence on English pages", () => {
    expect(problemText(conflict, en.errors, "en")).toBe(
      "Upload at least one document before submitting.",
    );
  });

  it("prefers the action's own sentence on Romanian pages, then the status", () => {
    expect(problemText(conflict, ro.errors, "ro", { 409: "Specific" })).toBe(
      "Specific",
    );
    expect(problemText(conflict, ro.errors, "ro")).toBe(ro.errors[409]);
  });

  it("falls back to the status sentence when the detail is not text", () => {
    const invalid = { status: 422, error: { detail: [{ msg: "bad" }] } };
    expect(problemText(invalid, en.errors, "en")).toBe(en.errors[422]);
  });

  it("names unknown statuses", () => {
    expect(problemText({ status: 418 }, en.errors, "en")).toBe(
      "Something went wrong (status 418). Try again.",
    );
  });
});
