import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MoveWorkoutModal } from "./MoveWorkoutModal";

describe("MoveWorkoutModal", () => {
  const fakeWos = [
    { id: 1, week_number: 1, day_of_week: "Monday", title: "Easy Aerobic Run", duration_minutes: 45, distance_km: 8 },
    { id: 2, week_number: 1, day_of_week: "Wednesday", title: "Intervals", duration_minutes: 50, distance_km: 9 },
  ];

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <MoveWorkoutModal
        isOpen={false}
        onClose={vi.fn()}
        sourceDay="Monday"
        weekNumber={1}
        weekWos={fakeWos}
        lang="en"
        onSwapDays={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders target days and differentiates rest day vs active workout day", () => {
    render(
      <MoveWorkoutModal
        isOpen={true}
        onClose={vi.fn()}
        sourceDay="Monday"
        weekNumber={1}
        weekWos={fakeWos}
        lang="en"
        onSwapDays={vi.fn()}
      />
    );

    expect(screen.getByText("Move or Swap Workout")).toBeInTheDocument();
    // Tuesday is a rest day (0 workouts)
    expect(screen.getByText("Tuesday")).toBeInTheDocument();
    // Wednesday has an active workout
    expect(screen.getByText("Wednesday")).toBeInTheDocument();
    expect(screen.getByText(/Intervals/)).toBeInTheDocument();
  });

  it("calls onSwapDays when clicking a target day", () => {
    const onSwapDays = vi.fn();
    const onClose = vi.fn();

    render(
      <MoveWorkoutModal
        isOpen={true}
        onClose={onClose}
        sourceDay="Monday"
        weekNumber={1}
        weekWos={fakeWos}
        lang="en"
        onSwapDays={onSwapDays}
      />
    );

    // Click Tuesday to move Monday's workout to Tuesday (rest day)
    const tuesdayTarget = screen.getByText("Tuesday").closest("div[style*='cursor: pointer']");
    expect(tuesdayTarget).toBeTruthy();
    fireEvent.click(tuesdayTarget!);

    expect(onSwapDays).toHaveBeenCalledWith("Monday", "Tuesday", 1);
    expect(onClose).toHaveBeenCalled();
  });

  it("supports Vietnamese translation", () => {
    render(
      <MoveWorkoutModal
        isOpen={true}
        onClose={vi.fn()}
        sourceDay="Monday"
        weekNumber={1}
        weekWos={fakeWos}
        lang="vi"
        onSwapDays={vi.fn()}
      />
    );

    expect(screen.getByText("Di chuyển hoặc Đổi ngày tập")).toBeInTheDocument();
    expect(screen.getByText("Thứ Ba")).toBeInTheDocument();
  });
});

describe("MoveWorkoutModal — move one workout", () => {
  // Plan starts Mon 2026-09-07; today Wed 2026-09-23 = week 3.
  const plan = { start_date: "2026-09-07", total_weeks: 12 };
  const today = new Date(2026, 8, 23);
  const all = [
    { id: 1, week_number: 3, day_of_week: "Thursday", title: "Tempo", duration_minutes: 50 },
    { id: 2, week_number: 3, day_of_week: "Thursday", title: "Strength", duration_minutes: 30 },
    { id: 3, week_number: 3, day_of_week: "Saturday", title: "Long Run", duration_minutes: 120 },
    { id: 4, week_number: 4, day_of_week: "Tuesday", title: "Easy", duration_minutes: 40 },
  ];
  const base = {
    isOpen: true, onClose: vi.fn(), sourceDay: "Thursday", weekNumber: 3, lang: "en",
    onSwapDays: vi.fn(), plan, today, allWorkouts: all,
    weekWos: all.filter((w) => w.week_number === 3),
  };

  it("offers the move mode only when onMoveWorkout is given", () => {
    const { rerender } = render(<MoveWorkoutModal {...base} />);
    expect(screen.queryByText("Move one workout")).toBeNull();
    rerender(<MoveWorkoutModal {...base} onMoveWorkout={vi.fn()} />);
    expect(screen.getByText("Move one workout")).toBeInTheDocument();
  });

  it("on a double day asks which session, then moves it to next week", () => {
    const onMoveWorkout = vi.fn();
    render(<MoveWorkoutModal {...base} onMoveWorkout={onMoveWorkout} />);
    fireEvent.click(screen.getByText("Move one workout"));
    expect(screen.getByText("Which session?")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Strength/ }));
    fireEvent.click(screen.getByRole("button", { name: "Next week" }));
    fireEvent.click(screen.getByRole("button", { name: /^Monday/ }));
    expect(onMoveWorkout).toHaveBeenCalledWith(2, 4, "Monday");
  });

  it("disables past days and hints double days", () => {
    render(<MoveWorkoutModal {...base} onMoveWorkout={vi.fn()} />);
    fireEvent.click(screen.getByText("Move one workout"));
    fireEvent.click(screen.getByRole("button", { name: /Tempo/ }));
    expect(screen.getByRole("button", { name: /^Monday/ })).toBeDisabled(); // week 3 Monday is past
    expect(screen.getByRole("button", { name: /^Saturday/ })).toHaveTextContent("+1 → double day");
  });

  it("hides week tabs for a far week (same-week targets only)", () => {
    const far = [{ id: 9, week_number: 8, day_of_week: "Tuesday", title: "Easy", duration_minutes: 40 }];
    render(
      <MoveWorkoutModal {...base} sourceDay="Tuesday" weekNumber={8} weekWos={far} allWorkouts={far} onMoveWorkout={vi.fn()} />
    );
    fireEvent.click(screen.getByText("Move one workout"));
    expect(screen.queryByRole("button", { name: "Next week" })).toBeNull();
  });

  it("does not offer an earlier/invalid week when the plan hasn't started yet", () => {
    // Plan starts Mon 2026-09-28, a week after today (Wed 2026-09-23) -- the
    // backend's unclamped current_week is 0, so only week 1 ("Next week") is
    // a valid target; there is no "This week" (week 0) or week-2 option.
    const futurePlan = { start_date: "2026-09-28", total_weeks: 12 };
    const wos = [{ id: 5, week_number: 1, day_of_week: "Tuesday", title: "Easy", duration_minutes: 40 }];
    const onMoveWorkout = vi.fn();
    render(
      <MoveWorkoutModal
        {...base}
        plan={futurePlan}
        sourceDay="Tuesday"
        weekNumber={1}
        weekWos={wos}
        allWorkouts={wos}
        onMoveWorkout={onMoveWorkout}
      />
    );
    fireEvent.click(screen.getByText("Move one workout"));
    expect(screen.queryByRole("button", { name: "This week" })).toBeNull();
    const weekTabButtons = screen.queryAllByRole("button", { name: /^(This week|Next week)$/ });
    expect(weekTabButtons).toHaveLength(1);
    expect(weekTabButtons[0]).toHaveTextContent("Next week");

    fireEvent.click(screen.getByRole("button", { name: /^Monday/ }));
    expect(onMoveWorkout).toHaveBeenCalledWith(5, 1, "Monday");
  });
});
