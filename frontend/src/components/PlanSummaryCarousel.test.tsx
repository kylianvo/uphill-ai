/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PlanSummaryCarousel from "./PlanSummaryCarousel";
import { planWeeklyVolumes, daysToRace } from "../utils/planSummary";

beforeEach(() => {
  (globalThis as any).IntersectionObserver = class { observe() {} disconnect() {} unobserve() {} };
});

const wo = (week: number, mins: number, extra: any = {}) => ({ week_number: week, duration_minutes: mins, distance_km: 5, phase: "Base", day_of_week: "Monday", ...extra });

describe("planWeeklyVolumes", () => {
  it("marks missing weeks as not generated", () => {
    const v = planWeeklyVolumes([wo(1, 60), wo(3, 120)], 4);
    expect(v.map((w) => w.generated)).toEqual([true, false, true, false]);
    expect(v[2].hours).toBe(2);
  });
});

describe("daysToRace", () => {
  const now = new Date(2026, 9, 1, 15, 0);
  it("is 0 on race day", () => expect(daysToRace("2026-10-01", now)).toBe(0));
  it("is null (never negative) after the race", () => expect(daysToRace("2026-09-20", now)).toBeNull());
  it("counts forward", () => expect(daysToRace("2026-10-11", now)).toBe(10));
});

describe("PlanSummaryCarousel", () => {
  const props: any = {
    activePlan: { race_name: "UTMB", race_date: "2099-01-01", total_weeks: 3 },
    workouts: [wo(1, 60, { is_completed: 1 })],
    selectedWeek: 1, maxGeneratedWeek: 1, distanceKm: 100, elevationM: 5000,
    goalPill: <span>pill</span>,
    onOpenPaceStrategy: vi.fn(), onOpenGoalDeterminer: vi.fn(), onOpenNutrition: vi.fn(),
  };
  it("labels dots and opens race tools", () => {
    render(<PlanSummaryCarousel {...props} />);
    for (const l of ["Show volume", "Show race and goal", "Show this week", "Show phase"]) {
      expect(screen.getByLabelText(l)).toBeTruthy();
    }
    fireEvent.click(screen.getByText("pill"));
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Race tools" }));
    fireEvent.click(screen.getByText("Nutrition Lab"));
    expect(props.onOpenNutrition).toHaveBeenCalled();
  });

  it("opens the week review sheet", () => {
    render(<PlanSummaryCarousel {...props} reviewContent={<p>review body</p>} />);
    fireEvent.click(screen.getByRole("button", { name: "Review week" }));
    expect(screen.getByRole("dialog", { name: "Week 1 review" })).toBeTruthy();
    expect(screen.getByText("review body")).toBeTruthy();
  });
  it("does not nest the goal pill inside a button", () => {
    render(<PlanSummaryCarousel {...props} goalPill={<button>pillbtn</button>} />);
    expect(screen.getByText("pillbtn").closest("[role=button]")).toBeNull();
  });
});
