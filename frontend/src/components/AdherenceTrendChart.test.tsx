import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import AdherenceTrendChart, { computeSparklinePoints } from "./AdherenceTrendChart";

describe("computeSparklinePoints", () => {
  it("maps adherence_pct (0-1) to y coordinates within the given height", () => {
    const points = computeSparklinePoints(
      [
        { week_number: 4, adherence_pct: 0.5 },
        { week_number: 5, adherence_pct: 1.0 },
      ],
      { width: 100, height: 40, padding: 0 }
    );
    expect(points).toHaveLength(2);
    expect(points[0].x).toBeLessThan(points[1].x);
    expect(points[1].y).toBeLessThan(points[0].y); // higher adherence -> smaller y (closer to top)
  });

  it("returns an empty array for empty input", () => {
    expect(computeSparklinePoints([], { width: 100, height: 40 })).toEqual([]);
  });

  it("places a single point at the right edge", () => {
    const points = computeSparklinePoints([{ week_number: 5, adherence_pct: 0.7 }], { width: 100, height: 40, padding: 0 });
    expect(points).toHaveLength(1);
    expect(points[0].x).toBe(100);
  });
});

describe("AdherenceTrendChart Component", () => {
  it("renders trend line and shows tooltip on hover", () => {
    render(
      <AdherenceTrendChart
        trend={[
          { week_number: 1, adherence_pct: 0.8 },
          { week_number: 2, adherence_pct: 1.0 },
        ]}
        lang="en"
      />
    );

    expect(screen.queryByTestId("trend-tooltip")).toBeNull();

    const point1 = screen.getByLabelText(/Week 1: 80% adherence/i);
    fireEvent.mouseEnter(point1);

    const tooltip = screen.getByTestId("trend-tooltip");
    expect(tooltip).toBeDefined();
    expect(tooltip.textContent).toContain("Wk 1");
    expect(tooltip.textContent).toContain("80%");

    fireEvent.mouseLeave(point1);
    expect(screen.queryByTestId("trend-tooltip")).toBeNull();
  });
});
