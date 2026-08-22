import { describe, it, expect } from "vitest";
import { computeSparklinePoints } from "./AdherenceTrendChart";

describe("computeSparklinePoints", () => {
  it("maps adherence_pct (0-1) to y coordinates within the given height, most-recent-highest-x", () => {
    const points = computeSparklinePoints(
      [
        { week_number: 4, adherence_pct: 0.5 },
        { week_number: 5, adherence_pct: 1.0 },
      ],
      { width: 100, height: 40 }
    );
    expect(points).toHaveLength(2);
    expect(points[0].x).toBeLessThan(points[1].x);
    expect(points[1].y).toBeLessThan(points[0].y); // higher adherence -> smaller y (closer to top)
  });

  it("returns an empty array for empty input", () => {
    expect(computeSparklinePoints([], { width: 100, height: 40 })).toEqual([]);
  });

  it("places a single point at the right edge", () => {
    const points = computeSparklinePoints([{ week_number: 5, adherence_pct: 0.7 }], { width: 100, height: 40 });
    expect(points).toHaveLength(1);
    expect(points[0].x).toBe(100);
  });
});
