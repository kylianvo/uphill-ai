import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import WeeklyReview, { computeCreditedActual, type WeekReviewData } from "./WeeklyReview";

// Scenario: a matched long run cut short (planned 90min/15km/300m, only 40min/6km/100m
// recorded), an easy run ticked complete with no watch recording (planned 60min/10km/200m,
// credited at its planned figures since that's the best estimate available), and a missed
// interval session (planned 30min/5km/50m, credited nothing).
function baseReview(overrides: Partial<WeekReviewData> = {}): WeekReviewData {
  return {
    week_number: 3,
    planned: { duration_minutes: 180, distance_km: 30, elevation_gain_m: 550, workout_count: 3 },
    actual: {
      total_actual_km: 6,
      total_actual_minutes: 40,
      total_actual_vert_m: 100,
      matched_km: 6,
      matched_vert_m: 100,
      matched_count: 1,
      unplanned_km: 0,
      unplanned_hours: 0,
      unplanned_vert_m: 0,
      unplanned_count: 0,
    },
    completion_pct: 22,
    checkbox_completion_pct: 83,
    per_workout: [
      {
        workout_id: 1,
        day_of_week: "Monday",
        title: "Long Run",
        type: "long_run",
        planned: { duration_minutes: 90, distance_km: 15, elevation_gain_m: 300 },
        actual: { state: "matched", duration_minutes: 40, distance_km: 6, elevation_gain_m: 100 },
      },
      {
        workout_id: 2,
        day_of_week: "Wednesday",
        title: "Easy Run",
        type: "easy",
        planned: { duration_minutes: 60, distance_km: 10, elevation_gain_m: 200 },
        actual: { state: "checkbox_only", duration_minutes: null, distance_km: null, elevation_gain_m: null },
      },
      {
        workout_id: 3,
        day_of_week: "Friday",
        title: "Hill Repeats",
        type: "interval",
        planned: { duration_minutes: 30, distance_km: 5, elevation_gain_m: 50 },
        actual: { state: "missed", duration_minutes: null, distance_km: null, elevation_gain_m: null },
      },
    ],
    unplanned: [],
    missed: [{ day_of_week: "Friday", title: "Hill Repeats" }],
    coverage: { completed_count: 2, matched_count: 1, checkbox_only_count: 1 },
    narrative: { summary: "Solid week overall.", highlights: ["Recorded 6.0km on the long run"], watch: ["Long run cut well short of plan"] },
    ...overrides,
  };
}

describe("computeCreditedActual", () => {
  it("credits a matched workout with its real recorded figures and a checkbox-only workout with its planned figures, and nothing for a missed one", () => {
    const credited = computeCreditedActual(baseReview());
    // 40 (matched) + 60 (checkbox-only, planned) + 0 (missed) + 0 (unplanned)
    expect(credited.minutes).toBe(100);
    expect(credited.km).toBe(16);
    expect(credited.vertM).toBe(300);
    expect(credited.pct).toBe(56); // round(100 / 180 * 100)
  });

  it("adds unplanned volume on top of credited planned/recorded workouts", () => {
    const credited = computeCreditedActual(
      baseReview({ actual: { ...baseReview().actual, unplanned_km: 4, unplanned_hours: 0.5, unplanned_vert_m: 40 } })
    );
    expect(credited.minutes).toBe(130); // 100 + 30
    expect(credited.km).toBe(20); // 16 + 4
    expect(credited.vertM).toBe(340); // 300 + 40
  });
});

describe("WeeklyReview", () => {
  it("renders nothing when there is no data", () => {
    const { container } = render(<WeeklyReview data={null} lang="en" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the credited planned-vs-actual breakdown, per-workout states, and narrative", () => {
    render(<WeeklyReview data={baseReview()} lang="en" />);

    expect(screen.getByText(/Logged as complete: 83%/)).toBeInTheDocument();
    expect(screen.getByText(/Completion: 56%/)).toBeInTheDocument();
    expect(screen.getByText("1.7 / 3.0 hrs")).toBeInTheDocument();
    expect(screen.getByText("16.0 / 30.0 km")).toBeInTheDocument();
    expect(screen.getByText("300 / 550 m")).toBeInTheDocument();

    expect(screen.getByText("This Week's Sessions")).toBeInTheDocument();
    expect(screen.getByText("Recorded")).toBeInTheDocument();
    expect(screen.getByText("Logged, no recording")).toBeInTheDocument();
    expect(screen.getByText("Missed")).toBeInTheDocument();
    expect(screen.getByText("Recorded 6.0km on the long run")).toBeInTheDocument();
    expect(screen.getByText("Long run cut well short of plan")).toBeInTheDocument();
  });

  it("does not show the checkbox-vs-credited divergence note when the two figures match", () => {
    render(<WeeklyReview data={baseReview({ checkbox_completion_pct: 56 })} lang="en" />);
    expect(screen.queryByText(/Logged as complete/)).not.toBeInTheDocument();
  });

  it("shows an unplanned activity as its own distinct entry, separate from planned workouts", () => {
    render(
      <WeeklyReview
        data={baseReview({ unplanned: [{ activity_id: 99, distance_km: 4, duration_seconds: 1200, activity_type: "Run" }] })}
        lang="en"
      />
    );

    expect(screen.getByText("Unplanned Activities")).toBeInTheDocument();
    expect(screen.getByText("4.0 km · 20 min")).toBeInTheDocument();
    expect(screen.getByText("Unplanned")).toBeInTheDocument();
  });

  it("renders Vietnamese copy, not English, when lang is vi", () => {
    render(<WeeklyReview data={baseReview()} lang="vi" />);

    expect(screen.getByText("Đã ghi nhận")).toBeInTheDocument();
    expect(screen.getByText("Đã đánh dấu, không có dữ liệu đồng hồ")).toBeInTheDocument();
    expect(screen.getByText("Bỏ lỡ")).toBeInTheDocument();
    expect(screen.queryByText("Recorded")).not.toBeInTheDocument();
  });
});
