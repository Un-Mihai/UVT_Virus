const dollars = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const counts = new Intl.NumberFormat("en-US");

const clock = new Intl.DateTimeFormat("en-GB", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  timeZone: "UTC",
});

/** Cents for normal amounts; fractions of a cent keep two significant digits ($0.000013). */
export function formatUsd(value: number): string {
  if (value === 0 || Math.abs(value) >= 0.01) return dollars.format(value);
  return `$${value.toPrecision(2)}`.replace(/\.?0+$/, "");
}

export function formatCount(value: number): string {
  return counts.format(value);
}

export function formatDuration(milliseconds: number): string {
  return milliseconds < 1000
    ? `${milliseconds} ms`
    : `${(milliseconds / 1000).toFixed(1)} s`;
}

export function formatClockUtc(iso: string): string {
  return `${clock.format(new Date(iso))} UTC`;
}
