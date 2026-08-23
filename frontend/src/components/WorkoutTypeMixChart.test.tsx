import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import WorkoutTypeMixChart, { computeBarLayout, labelFor } from "./WorkoutTypeMixChart";

describe("computeBarLayout", () => {
  it("calculates widthPct as true percentage out of 100", () => {
    const layout = computeBarLayout([
      { type: "easy_run", count: 10, pct: 0.5 },
      { type: "long_run", count: 5, pct: 0.25 },
    ]);
    expect(layout).toHaveLength(2);
    expect(layout[0].widthPct).toBe(50);
    expect(layout[1].widthPct).toBe(25);
  });

  it("handles empty array gracefully", () => {
    expect(computeBarLayout([])).toEqual([]);
  });
});

describe("labelFor canonical types", () => {
  it("maps plan workout types to canonical display names", () => {
    expect(labelFor("easy_run")).toBe("Easy");
    expect(labelFor("easy")).toBe("Easy");
    expect(labelFor("strength")).toBe("Strength");
    expect(labelFor("tempo")).toBe("Tempo");
    expect(labelFor("long_run")).toBe("Long Run");
    expect(labelFor("muscular_endurance")).toBe("Muscular Endurance");
    expect(labelFor("me_session")).toBe("Muscular Endurance");
    expect(labelFor("interval")).toBe("Interval");
  });
});

describe("WorkoutTypeMixChart Component", () => {
  it("shows tooltip on row hover", () => {
    render(
      <WorkoutTypeMixChart
        mix={[
          { type: "easy_run", count: 8, pct: 0.8 },
          { type: "tempo", count: 2, pct: 0.2 },
        ]}
        lang="en"
      />
    );

    expect(screen.queryByTestId("mix-tooltip")).toBeNull();

    const row = screen.getByLabelText(/Easy: 8 workouts/i);
    fireEvent.mouseEnter(row);

    const tooltip = screen.getByTestId("mix-tooltip");
    expect(tooltip).toBeDefined();
    expect(tooltip.textContent).toContain("Easy");
    expect(tooltip.textContent).toContain("8 workouts (80%)");

    fireEvent.mouseLeave(row);
    expect(screen.queryByTestId("mix-tooltip")).toBeNull();
  });
});
