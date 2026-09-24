import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import ScheduleRebuildCard, { POLL_LIMIT_MS, POLL_MS } from "./ScheduleRebuildCard";

const card = {
  proposal_id: 11, status: "generating", week: 3, from_day: "Thursday", rationale: "Legs are heavy.",
  plan_start_date: "2026-09-07", race_date: null,
};

const diff = {
  week: 3, from_day: "Thursday",
  totals: { before: { min: 280, km: 46.7, vert: 0 }, after: { min: 190, km: 31.7, vert: 0 } },
  days: [
    { day: "Monday", kept: [{ id: 1, title: "Easy", duration_minutes: 40 }], before: [], after: [] },
    { day: "Tuesday", kept: [], before: [], after: [] },
    { day: "Wednesday", kept: [], before: [], after: [] },
    { day: "Thursday", kept: [], before: [{ id: 3, title: "Tempo", duration_minutes: 50 }],
      after: [{ week_number: 3, day_of_week: "Thursday", title: "Easy Recovery", type: "Easy", duration_minutes: 35, target_zone: "Zone 2", phase: "Base" }] },
    { day: "Friday", kept: [], before: [], after: [] },
    { day: "Saturday", kept: [], before: [], after: [] },
    { day: "Sunday", kept: [], before: [{ id: 5, title: "Long Run", duration_minutes: 120 }],
      after: [{ week_number: 3, day_of_week: "Sunday", title: "Long Run", type: "Long Run", duration_minutes: 90, target_zone: "Zone 2", phase: "Base" }] },
  ],
};

function detail(status: string, extra: Record<string, unknown> = {}) {
  return { id: 11, kind: "rebuild", status, diff: status === "generating" ? {} : diff, warnings: [], stale_reason: null, ...extra };
}

// Each GET /proposals/11 answers the next queued body; POSTs answer `post`;
// anything else (WorkoutCard's workout-types fetch) gets [].
function mockFetch(gets: unknown[], post?: { status: number; body: unknown }) {
  const queue = [...gets];
  const fn = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
    const u = String(url);
    if (u.includes("/proposals/11") && (!init || !init.method || init.method === "GET")) {
      const body = queue.length > 1 ? queue.shift() : queue[0];
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
    }
    if (u.includes("/proposals/11/") && post) {
      return Promise.resolve(new Response(JSON.stringify(post.body), { status: post.status }));
    }
    return Promise.resolve(new Response("[]", { status: 200 }));
  });
  global.fetch = fn;
  return fn;
}

const getCalls = (fn: ReturnType<typeof vi.fn>) =>
  fn.mock.calls.filter(([u, init]) => String(u).endsWith("/proposals/11") && !(init as RequestInit | undefined)?.method).length;

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("ScheduleRebuildCard", () => {
  it("shows the before/after diff, totals and Apply once the draft is ready", async () => {
    mockFetch([detail("proposed")]);
    render(<ScheduleRebuildCard data={{ ...card, status: "proposed" }} lang="en" />);
    expect(await screen.findByText(/Tempo · 50′ → Easy Recovery · 35′/)).toBeInTheDocument();
    expect(screen.getByText(/280 min · 46.7 km/)).toBeInTheDocument();
    expect(screen.getByText(/190 min · 31.7 km/)).toBeInTheDocument();
    expect(screen.getByText(/kept/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply" })).toBeEnabled();
  });

  it("polls while generating and stops when the draft is ready", async () => {
    vi.useFakeTimers();
    const fn = mockFetch([detail("generating"), detail("proposed")]);
    render(<ScheduleRebuildCard data={card} lang="en" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(0); });
    expect(screen.getByText("Drafting week 3…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Discard" })).toBeEnabled();
    await act(async () => { await vi.advanceTimersByTimeAsync(POLL_MS); });
    expect(screen.getByRole("button", { name: "Apply" })).toBeInTheDocument();
    const calls = getCalls(fn);
    await act(async () => { await vi.advanceTimersByTimeAsync(POLL_MS * 3); });
    expect(getCalls(fn)).toBe(calls);
  });

  it("gives up after the poll limit and shows the failure", async () => {
    vi.useFakeTimers();
    mockFetch([detail("generating")]);
    render(<ScheduleRebuildCard data={card} lang="en" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(POLL_LIMIT_MS + POLL_MS); });
    expect(screen.getByText("Couldn't draft this week — ask the coach to try again.")).toBeInTheDocument();
  });

  it("stops polling on a failed draft", async () => {
    vi.useFakeTimers();
    const fn = mockFetch([detail("failed", { stale_reason: "generation_error" })]);
    render(<ScheduleRebuildCard data={card} lang="en" />);
    await act(async () => { await vi.advanceTimersByTimeAsync(POLL_MS * 3); });
    expect(getCalls(fn)).toBe(1);
    expect(screen.getByText("Couldn't draft this week — ask the coach to try again.")).toBeInTheDocument();
  });

  it("applies and reports the refreshed workouts", async () => {
    mockFetch([detail("proposed")], { status: 200, body: { status: "applied", result: { inserted: 2 }, workouts: [{ id: 9 }] } });
    const onApplied = vi.fn();
    render(<ScheduleRebuildCard data={{ ...card, status: "proposed" }} lang="en" onApplied={onApplied} />);
    fireEvent.click(await screen.findByRole("button", { name: "Apply" }));
    expect(await screen.findByText("Applied ✓")).toBeInTheDocument();
    expect(onApplied).toHaveBeenCalledWith([{ id: 9 }]);
  });

  it("shows Out of date with the reason on a stale apply", async () => {
    mockFetch([detail("proposed")], { status: 409, body: { status: "stale", stale_reason: "STALE_rolled_over" } });
    render(<ScheduleRebuildCard data={{ ...card, status: "proposed" }} lang="en" />);
    fireEvent.click(await screen.findByRole("button", { name: "Apply" }));
    expect(await screen.findByText("Out of date")).toBeInTheDocument();
    expect(screen.getByText(/The first day of this draft has already passed/)).toBeInTheDocument();
  });

  it("expands a day to the full new workout", async () => {
    mockFetch([detail("proposed")]);
    render(<ScheduleRebuildCard data={{ ...card, status: "proposed" }} lang="en" />);
    fireEvent.click(await screen.findByText(/Tempo · 50′ → Easy Recovery · 35′/));
    expect(await screen.findAllByText("Easy Recovery")).not.toHaveLength(0);
  });
});
