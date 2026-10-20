import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

  it("formats rep fields on other run types", () => {
    expect(
      formatIntervalSummary({ type: "Tempo", interval_reps: 8, interval_rep_value: 12, interval_rep_unit: "s" })
    ).toBe("8x12s");
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

  it("asks why a missed session was missed and reports the chosen reason", () => {
    const onMarkMissed = vi.fn();
    const missed = { ...wo, is_missed: 1 };
    render(
      <WorkoutCard wo={missed} isMobile={false} lang="en" getWorkoutDate={() => ""} onMarkMissed={onMarkMissed} />
    );
    fireEvent.click(screen.getByRole("button", { name: "Sick" }));
    expect(onMarkMissed).toHaveBeenCalledWith(missed.id, true, "sick");
  });

  it("shows the Vietnamese reason chips and marks the saved one", () => {
    const missed = { ...wo, is_missed: 1, missed_reason: "busy" };
    render(<WorkoutCard wo={missed} isMobile={false} lang="vi" getWorkoutDate={() => ""} onMarkMissed={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Bận" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Ốm" })).toHaveAttribute("aria-pressed", "false");
  });

  it("hides the reason chips for a session that is not missed", () => {
    render(<WorkoutCard wo={wo} isMobile={false} lang="en" getWorkoutDate={() => ""} onMarkMissed={vi.fn()} />);
    expect(screen.queryByTestId("missed-reason-chips")).not.toBeInTheDocument();
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

  it("shows execution guide expanded by default when card is expanded with 1-click header toggle", () => {
    const woWithExecution = {
      ...wo,
      description: "Process: Warm up 10 min easy jog → 4 x 6min @ Zone 4, 2min jog recovery → cool down 10 min stretch",
    };
    render(
      <WorkoutCard
        wo={woWithExecution}
        isMobile={false}
        lang="en"
        getWorkoutDate={() => "Sep 2"}
        defaultExpanded={false}
      />
    );

    // Click on the workout header title to expand the card in 1 click
    const titleElement = screen.getByText("Hill Repeats");
    fireEvent.click(titleElement);

    // The execution step should be visible immediately without a second click
    expect(screen.getByText("4 x 6min @ Zone 4, 2min jog recovery")).toBeInTheDocument();
    // And "Hide guide" toggle is visible
    expect(screen.getByText("Hide guide")).toBeInTheDocument();
  });
});

describe("WorkoutCard priority", () => {
  const base = {
    id: 9, day_of_week: "Monday", type: "Tempo", title: "Tempo", duration_minutes: 45,
    target_zone: "Zone 3", approved_at: "2026-10-01",
  };
  const props = { isMobile: false, lang: "en", getWorkoutDate: () => "Oct 1" };

  it("shows PRIORITY only for is_priority under V2", () => {
    const { rerender } = render(<WorkoutCard {...props} wo={{ ...base, is_priority: true }} shellV2 />);
    expect(screen.getByText("PRIORITY")).toBeInTheDocument();
    rerender(<WorkoutCard {...props} wo={{ ...base, is_priority: false }} shellV2 />);
    expect(screen.queryByText("PRIORITY")).toBeNull();
    rerender(<WorkoutCard {...props} wo={{ ...base, is_priority: true }} />);
    expect(screen.queryByText("PRIORITY")).toBeNull();
  });

  it("shows no label when is_priority is undefined under V2", () => {
    render(<WorkoutCard {...props} wo={base} shellV2 />);
    expect(screen.queryByText("PRIORITY")).toBeNull();
  });

  it("shows the eyebrow only under V2", () => {
    render(<WorkoutCard {...props} wo={base} shellV2 eyebrow="TODAY" />);
    expect(screen.getByText("TODAY")).toBeInTheDocument();
  });

  it("coach edit sends is_priority", () => {
    const onEdit = vi.fn();
    render(<WorkoutCard {...props} wo={base} isCoachActingAsAthlete onEditWorkout={onEdit} />);
    fireEvent.click(screen.getByTitle("Edit"));
    fireEvent.click(screen.getByLabelText("Priority"));
    fireEvent.click(screen.getByText("Save"));
    expect(onEdit).toHaveBeenCalledWith(9, expect.objectContaining({ is_priority: true }));
  });
});

describe("trail and sprint metrics", () => {
  const trail = { id: 111, day_of_week: "Saturday", title: "Núi Dinh Long Run", type: "Long Run", target_zone: "Zone 2", duration_minutes: 210,
    distance_km: 26, elevation_gain_m: 1560, target_pace: "8:26 - 7:44 /km", approved_at: "2026-10-17" };
  it("renders rep chips on Easy runs and omits maximum-effort pace", () => {
    render(<WorkoutCard wo={{ ...trail, title: "Hill Sprints", type: "Easy", target_zone: "Zone 5", interval_reps: 8, interval_rep_value: 10, interval_rep_unit: "s" }} isMobile={false} lang="en" getWorkoutDate={() => ""} readOnly />);
    expect(screen.getByText("8x10s")).toBeInTheDocument();
    expect(screen.queryByText(trail.target_pace)).not.toBeInTheDocument();
  });
  it("labels trail pace and estimated climbing on the card", () => {
    render(<WorkoutCard wo={trail} isMobile={false} lang="en" getWorkoutDate={() => ""} readOnly />);
    expect(screen.getByText(/Trail pace/)).toBeInTheDocument();
    expect(screen.getByText(/1560.*m/)).toBeInTheDocument();
    expect(screen.getByText(/~26.*km/)).toBeInTheDocument();
  });
  it("renders Vietnamese trail labels", () => {
    render(<WorkoutCard wo={trail} isMobile={false} lang="vi" getWorkoutDate={() => ""} readOnly />);
    expect(screen.getByText(/Pace trail/)).toBeInTheDocument();
    expect(screen.getByText(/D\+ ước tính/)).toBeInTheDocument();
  });
});

describe("Easy hill-sprint editing and aerobic pace", () => {
  const wo = { id: 112, day_of_week: "Saturday", title: "Easy + Hill Sprints", type: "Easy", target_zone: "Zone 2",
    duration_minutes: 80, distance_km: 9.9, elevation_gain_m: 594, target_pace: "8:26 - 7:44 /km",
    interval_reps: 8, interval_rep_value: 10, interval_rep_unit: "s", approved_at: "2026-10-17" };
  it("keeps the aerobic trail pace separate from the sprint rep chip", () => {
    render(<WorkoutCard wo={wo} isMobile={false} lang="en" getWorkoutDate={() => ""} readOnly />);
    expect(screen.getByText("8x10s")).toBeInTheDocument();
    expect(screen.getByText(`Trail pace: ${wo.target_pace}`)).toBeInTheDocument();
  });
  it("preserves Easy-run reps through ordinary coach edits", () => {
    const onEdit = vi.fn();
    render(<WorkoutCard wo={wo} isMobile={false} lang="en" getWorkoutDate={() => ""} isCoachActingAsAthlete onEditWorkout={onEdit} />);
    fireEvent.click(screen.getByTitle("Edit"));
    fireEvent.click(screen.getByLabelText("Priority"));
    fireEvent.click(screen.getByText("Save"));
    expect(onEdit).toHaveBeenCalledWith(112, expect.objectContaining({ interval_reps: 8, interval_rep_value: 10, interval_rep_unit: "s" }));
  });
});
