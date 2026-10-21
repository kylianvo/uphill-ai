import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import MilestonePath from "./MilestonePath";
import type { MilestoneItem, PlanMilestones } from "../lib/beginnerMilestones";

const item = (key: string, w: [number, number], at: string | null = null, source: MilestoneItem["source"] = at ? "auto" : null): MilestoneItem => ({
  key, kind: "jog_min", threshold: 5, stage: "A", typical_weeks: w, achieved_at: at, source,
});
const base = (over: Partial<PlanMilestones> = {}): PlanMilestones => ({
  target: "5k", has_event: false, next_key: "jog_10",
  items: [item("first_session", [1, 1], "2026-10-06"), item("jog_5", [3, 5], "2026-10-12"), item("jog_10", [4, 6]), item("first_5k", [9, 12])],
  ...over,
});

beforeEach(() => { try { localStorage.clear(); } catch { /* ignore */ } });

describe("MilestonePath", () => {
  it("shows reached rows and the next milestone with its typical weeks", () => {
    render(<MilestonePath milestones={base()} lang="en" planId={1} weeksToEvent={null} onMark={vi.fn()} onUndo={vi.fn()} onUpgrade={vi.fn()} />);
    expect(screen.getByText("First 5K · 2 of 4 milestones")).toBeInTheDocument();
    expect(screen.getByText("10 min unbroken jog")).toBeInTheDocument();
    expect(screen.getByText("usually around week 4–6")).toBeInTheDocument();
  });
  it("asks to confirm before marking the next milestone", () => {
    const onMark = vi.fn();
    render(<MilestonePath milestones={base()} lang="en" planId={1} weeksToEvent={null} onMark={onMark} onUndo={vi.fn()} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "I did it" }));
    expect(onMark).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Yes, mark it" }));
    expect(onMark).toHaveBeenCalledWith("jog_10");
  });
  it("undoes an achieved row", () => {
    const onUndo = vi.fn();
    render(<MilestonePath milestones={base()} lang="en" planId={1} weeksToEvent={null} onMark={vi.fn()} onUndo={onUndo} onUpgrade={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Undo 5 min unbroken jog" }));
    expect(onUndo).toHaveBeenCalledWith("jog_5");
  });
  it("offers Next: First 10K once first_5k is reached on a 5K target", () => {
    const onUpgrade = vi.fn();
    const ms = base({ next_key: null, items: [item("first_5k", [9, 12], "2026-11-20")] });
    render(<MilestonePath milestones={ms} lang="en" planId={1} weeksToEvent={null} onMark={vi.fn()} onUndo={vi.fn()} onUpgrade={onUpgrade} />);
    fireEvent.click(screen.getByRole("button", { name: "Next: First 10K" }));
    expect(onUpgrade).toHaveBeenCalled();
  });
  it("celebrates a newly reached milestone once", () => {
    const props = { milestones: base(), lang: "en" as const, planId: 7, weeksToEvent: null, onMark: vi.fn(), onUndo: vi.fn(), onUpgrade: vi.fn() };
    const { unmount } = render(<MilestonePath {...props} />);
    expect(screen.getByRole("status")).toHaveTextContent("5 min unbroken jog");
    unmount();
    render(<MilestonePath {...props} />);
    expect(screen.queryByRole("status")).toBeNull();
  });
  it("does not celebrate baseline rows", () => {
    const ms = base({ items: [item("jog_5", [3, 5], "2026-10-06", "baseline"), item("jog_10", [4, 6])] });
    render(<MilestonePath milestones={ms} lang="en" planId={9} weeksToEvent={null} onMark={vi.fn()} onUndo={vi.fn()} onUpgrade={vi.fn()} />);
    expect(screen.queryByRole("status")).toBeNull();
  });
});
