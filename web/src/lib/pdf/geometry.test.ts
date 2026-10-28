import { expect, it } from "vitest";

import { rectStyle } from "./geometry";

it("turns PDF points into percentages of the page", () => {
  expect(
    rectStyle([59.5, 84.2, 297.5, 168.4], { width: 595, height: 842 }),
  ).toEqual({
    left: "10.000%",
    top: "10.000%",
    width: "40.000%",
    height: "10.000%",
  });
});

it("keeps boxes inside the page", () => {
  expect(rectStyle([-10, 0, 700, 900], { width: 595, height: 842 })).toEqual({
    left: "0.000%",
    top: "0.000%",
    width: "100.000%",
    height: "100.000%",
  });
});
