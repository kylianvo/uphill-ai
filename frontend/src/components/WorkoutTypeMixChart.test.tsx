import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import WorkoutTypeMixChart, { computeBarLayout } from "./WorkoutTypeMixChart";

describe("computeBarLayout", () => {
  it("normalizes highest pct bar to widthPct 100", () => {
    const layout = computeBarLayout([
      { type: "easy_run", count: 10, pct: 0.5 },
      { type: "long_run", count: 5, pct: 0.25 },
    ]);
    expect(layout).toHaveLength(2);
    expect(layout[0].widthPct).toBe(100);
    expect(layout[1].widthPct).toBe(50);
  });

  it("handles empty array gracefully", () => {
    expect(computeBarLayout([])).toEqual([]);
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

    const row = screen.getByLabelText(/Easy run: 8 workouts/i);
    fireEvent.mouseEnter(row);

    const tooltip = screen.getByTestId("mix-tooltip");
    expect(tooltip).toBeDefined();
    expect(tooltip.textContent).toContain("Easy run");
    expect(tooltip.textContent).toContain("8 workouts (80%)");

    fireEvent.mouseLeave(row);
    expect(screen.queryByTestId("mix-tooltip")).toBeNull();
  });
});
