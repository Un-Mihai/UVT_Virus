import { describe, expect, it } from "vitest";

import { formatClockUtc, formatDuration, formatUsd } from "./format";

describe("formatUsd", () => {
  it("shows cents for normal amounts", () => {
    expect(formatUsd(5)).toBe("$5.00");
    expect(formatUsd(0.0123)).toBe("$0.01");
    expect(formatUsd(0)).toBe("$0.00");
  });

  it("keeps fractions of a cent visible", () => {
    expect(formatUsd(0.000013)).toBe("$0.000013");
    expect(formatUsd(0.0042)).toBe("$0.0042");
    expect(formatUsd(0.0005)).toBe("$0.0005");
  });
});

describe("formatDuration", () => {
  it("switches from milliseconds to seconds at one second", () => {
    expect(formatDuration(820)).toBe("820 ms");
    expect(formatDuration(1430)).toBe("1.4 s");
  });
});

describe("formatClockUtc", () => {
  it("prints UTC wall-clock time", () => {
    expect(formatClockUtc("2026-10-28T09:05:07.120Z")).toBe("09:05:07 UTC");
  });
});
