import { describe, it, expect } from "vitest";
import { computeBarLayout } from "./WorkoutTypeMixChart";

describe("computeBarLayout", () => {
  it("scales widthPct relative to the largest entry", () => {
    const layout = computeBarLayout([
      { type: "long_run", pct: 0.4 },
      { type: "tempo", pct: 0.2 },
    ]);
    expect(layout[0]).toEqual({ type: "long_run", pct: 0.4, widthPct: 100 });
    expect(layout[1]).toEqual({ type: "tempo", pct: 0.2, widthPct: 50 });
  });

  it("caps the result at maxBars entries", () => {
    const mix = Array.from({ length: 10 }, (_, i) => ({ type: `type_${i}`, pct: (10 - i) / 55 }));
    const layout = computeBarLayout(mix, 3);
    expect(layout).toHaveLength(3);
    expect(layout[0].type).toBe("type_0");
  });

  it("returns an empty array for empty input", () => {
    expect(computeBarLayout([])).toEqual([]);
  });
});
