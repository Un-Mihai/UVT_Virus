/** A page's size in PDF points, as the API measured it. */
export type PageBox = { width: number; height: number };

/** A highlight box ([x0, top, x1, bottom] in PDF points from the top-left corner) as CSS
 *  percentages of its page, so it stays in place at any rendered size. */
export function rectStyle(rect: number[], page: PageBox) {
  const [x0 = 0, top = 0, x1 = 0, bottom = 0] = rect;
  const clamp = (value: number, size: number) =>
    Math.min(Math.max(value, 0), size);
  const percent = (value: number, size: number) =>
    `${((value / size) * 100).toFixed(3)}%`;
  const left = clamp(x0, page.width);
  const upper = clamp(top, page.height);
  return {
    left: percent(left, page.width),
    top: percent(upper, page.height),
    width: percent(clamp(x1, page.width) - left, page.width),
    height: percent(clamp(bottom, page.height) - upper, page.height),
  };
}
