import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import WorkoutCard, { formatIntervalSummary } from "./WorkoutCard";

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

describe("WorkoutCard readOnly mode", () => {
  const wo = {
    id: 1,
    day_of_week: "Tuesday",
    title: "Hill Repeats",
    type: "Interval",
    target_zone: "Zone 4",
    duration_minutes: 45,
    distance_km: 8,
    description: "Warm-up. Main: 6x3min uphill Zone 4. Cool-down.",
    approved_at: "2026-01-01T00:00:00Z",
    source: "ai_generated",
    is_completed: false,
    is_missed: false,
  };

  it("shows descriptive content but hides every mutating control", () => {
    render(<WorkoutCard wo={wo} isMobile={false} lang="en" getWorkoutDate={() => "Sep 2"} readOnly defaultExpanded />);

    // Descriptive content stays
    expect(screen.getByText("Hill Repeats")).toBeInTheDocument();
    expect(screen.getByText("Sep 2")).toBeInTheDocument();

    // Mutating controls are gone
    expect(screen.queryByTitle("Mark complete")).not.toBeInTheDocument();
    expect(screen.queryByTitle("Mark missed")).not.toBeInTheDocument();
    expect(screen.queryByTitle("Edit")).not.toBeInTheDocument();
    expect(screen.queryByText(/How did it feel/)).not.toBeInTheDocument();
  });

  it("does not require onToggleComplete/onLogWorkout callbacks when readOnly", () => {
    expect(() =>
      render(<WorkoutCard wo={wo} isMobile={false} lang="en" getWorkoutDate={() => ""} readOnly />)
    ).not.toThrow();
  });

  it("keeps the Pending review badge in readOnly mode for an unapproved workout", () => {
    const pendingWo = { ...wo, approved_at: null };
    render(<WorkoutCard wo={pendingWo} isMobile={false} lang="en" getWorkoutDate={() => "Sep 2"} readOnly />);
    expect(screen.getByText("Pending review")).toBeInTheDocument();
  });
});
