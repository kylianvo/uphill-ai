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
