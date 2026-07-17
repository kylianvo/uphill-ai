import { describe, it, expect } from "vitest";
import { formatIntervalSummary } from "./WorkoutCard";

describe("formatIntervalSummary", () => {
  it("formats a clean single-block interval as reps x value + unit", () => {
    expect(
      formatIntervalSummary({ type: "Interval", interval_reps: 8, interval_rep_value: 12, interval_rep_unit: "s" })
    ).toBe("8x12s");
  });

  it("formats a distance-based rep block", () => {
    expect(
      formatIntervalSummary({ type: "Interval", interval_reps: 5, interval_rep_value: 400, interval_rep_unit: "m" })
    ).toBe("5x400m");
  });

  it("is case-insensitive on type", () => {
    expect(
      formatIntervalSummary({ type: "interval", interval_reps: 4, interval_rep_value: 3, interval_rep_unit: "min" })
    ).toBe("4x3min");
  });

  it("returns null for non-Interval types", () => {
    expect(
      formatIntervalSummary({ type: "Tempo", interval_reps: 8, interval_rep_value: 12, interval_rep_unit: "s" })
    ).toBeNull();
  });

  it("returns null when any field is missing", () => {
    expect(formatIntervalSummary({ type: "Interval", interval_reps: 8 })).toBeNull();
  });
});
