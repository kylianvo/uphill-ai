import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import MissedByDayChart, { zeroFillDays } from "./MissedByDayChart";

describe("zeroFillDays", () => {
  it("fills all 7 days in Monday-Sunday order, zero for absent days", () => {
    const filled = zeroFillDays([
      { day_of_week: "Wednesday", count: 3 },
      { day_of_week: "Monday", count: 5 },
    ]);
    expect(filled.map((d) => d.day_of_week)).toEqual([
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
      "Sunday",
    ]);
    expect(filled.find((d) => d.day_of_week === "Wednesday")?.count).toBe(3);
    expect(filled.find((d) => d.day_of_week === "Tuesday")?.count).toBe(0);
  });

  it("returns all-zero for empty input", () => {
    const filled = zeroFillDays([]);
    expect(filled.every((d) => d.count === 0)).toBe(true);
    expect(filled).toHaveLength(7);
  });
});

describe("MissedByDayChart Component", () => {
  it("shows tooltip on bar hover", () => {
    render(
      <MissedByDayChart
        missedByDay={[
          { day_of_week: "Monday", count: 2 },
          { day_of_week: "Wednesday", count: 1 },
        ]}
        lang="en"
      />
    );

    expect(screen.queryByTestId("missed-tooltip")).toBeNull();

    const monBar = screen.getByLabelText(/Monday: 2 missed/i);
    fireEvent.mouseEnter(monBar);

    const tooltip = screen.getByTestId("missed-tooltip");
    expect(tooltip).toBeDefined();
    expect(tooltip.textContent).toContain("Monday");
    expect(tooltip.textContent).toContain("2 missed");

    fireEvent.mouseLeave(monBar);
    expect(screen.queryByTestId("missed-tooltip")).toBeNull();
  });
});
