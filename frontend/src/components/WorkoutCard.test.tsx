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

  describe("Walk/Run sessions", () => {
    // The reported production complaint: the plan rendered the long-hand the model
    // wrote in the description ("3 min run, 1 min walk, 3 min run, 1 min walk, ...")
    // which the reader has to count. It should collapse to one glanceable line.
    it("renders the jog and walk intervals as a single pair", () => {
      expect(
        formatIntervalSummary({
          type: "Walk/Run",
          interval_reps: 5,
          interval_rep_value: 2,
          interval_rep_unit: "min",
          walk_interval_value: 1,
        })
      ).toBe("5 x 2min jog / 1min walk");
    });

    it("is case-insensitive on type", () => {
      expect(
        formatIntervalSummary({
          type: "walk/run",
          interval_reps: 3,
          interval_rep_value: 3,
          interval_rep_unit: "min",
          walk_interval_value: 1,
        })
      ).toBe("3 x 3min jog / 1min walk");
    });

    it("formats fractional intervals to one decimal", () => {
      expect(
        formatIntervalSummary({
          type: "Walk/Run",
          interval_reps: 6,
          interval_rep_value: 1.5,
          interval_rep_unit: "min",
          walk_interval_value: 2.5,
        })
      ).toBe("6 x 1.5min jog / 2.5min walk");
    });

    it("falls back to the plain rep form when no walk value was recorded", () => {
      expect(
        formatIntervalSummary({
          type: "Walk/Run",
          interval_reps: 4,
          interval_rep_value: 2,
          interval_rep_unit: "min",
        })
      ).toBe("4x2min");
    });
  });
});
