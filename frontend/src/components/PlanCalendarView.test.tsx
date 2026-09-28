import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PlanCalendarView from "./PlanCalendarView";

vi.mock("../hooks/useWorkoutTypes", () => ({ useWorkoutTypes: () => ({ types: [] }), resolveWorkoutInfo: () => null }));
vi.mock("./WorkoutCard", () => ({ default: () => <div>Workout details</div> }));

const workouts = [
  { id: 1, week_number: 1, day_of_week: "Monday", title: "Easy Run", type: "Easy Run", phase: "Base", duration_minutes: 40, distance_km: 6, target_zone: "Zone 2", is_completed: 0 },
  { id: 2, week_number: 1, day_of_week: "Sunday", title: "Long Run", type: "Long Run", phase: "Base", duration_minutes: 100, distance_km: 15, target_zone: "Zone 2", is_completed: 0 },
  { id: 3, week_number: 2, day_of_week: "Monday", title: "Recovery Run", type: "Recovery Run", phase: "Base", duration_minutes: 30, distance_km: 4, target_zone: "Zone 1", is_completed: 0 },
];
const dates = [new Date(2026,8,28), new Date(2026,9,4), new Date(2026,9,5)];
const props = { workouts, lang: "en", isMobile: false, focusWeek: 1, onWeekChange: vi.fn(), getWorkoutDateObj: (wo: {id: number}) => dates[wo.id-1], getWorkoutDate: () => "", onSwapDays: vi.fn(), onToggleComplete: vi.fn(), onLogWorkout: vi.fn() };

describe("weekly planning calendar", () => {
  it("opens the selected training week and totals days across a month boundary", () => {
    render(<PlanCalendarView {...props} />);
    expect(screen.getByRole("button", { name: "Week", exact: true })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getAllByText("~21 km").length).toBeGreaterThan(0);
    expect(screen.getByText("Long Run")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next week" }));
    expect(props.onWeekChange).toHaveBeenCalledWith(2);
    expect(screen.getByText("Recovery Run")).toBeInTheDocument();
    expect(screen.queryByText("Long Run")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Month", exact: true }));
    expect(screen.getByRole("button", { name: "Next month" })).toBeInTheDocument();
  });

  it("opens workout details using the keyboard", () => {
    render(<PlanCalendarView {...props} />);
    fireEvent.keyDown(screen.getByRole("button", { name: /Monday, September 28/ }), { key: "Enter" });
    expect(screen.getByText("Workout details")).toBeInTheDocument();
  });
});
