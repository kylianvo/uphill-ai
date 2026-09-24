import React from "react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ScheduleProposalCard from "./ScheduleProposalCard";

const data = {
  proposal_id: 7,
  status: "proposed",
  rationale: "You're travelling Thursday.",
  plan_start_date: "2026-09-07",
  race_date: null,
  operations: [{ op: "move", workout_id: 3, target_week: 4, target_day: "Monday" }],
  warnings: [{ code: "W2_volume_shift", params: { week: 3, before_minutes: 240, after_minutes: 180 } }],
  diff: [
    {
      workout_id: 3, from_week: 3, from_day: "Thursday", to_week: 4, to_day: "Monday",
      workout: { id: 3, week_number: 4, day_of_week: "Monday", title: "Tempo Run", type: "Tempo", duration_minutes: 50, target_zone: "Zone 3", phase: "base" },
    },
  ],
};

// WorkoutCard's useWorkoutTypes also fetches on mount -- answer it with [] and
// build a fresh Response per call (a Response body can only be read once).
function mockFetch(status: number, body: unknown) {
  global.fetch = vi.fn().mockImplementation((url: string) =>
    Promise.resolve(
      String(url).includes("/proposals/")
        ? new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } })
        : new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } })
    )
  );
}

afterEach(() => vi.restoreAllMocks());

describe("ScheduleProposalCard", () => {
  it("shows the move, rationale, warning and both buttons when proposed", () => {
    render(<ScheduleProposalCard data={data} lang="en" />);
    expect(screen.getByText("Proposed schedule change")).toBeInTheDocument();
    expect(screen.getByText(/Week 3 · Thursday/)).toBeInTheDocument();
    expect(screen.getByText(/Week 4 · Monday/)).toBeInTheDocument();
    expect(screen.getByText(/You're travelling Thursday/)).toBeInTheDocument();
    expect(screen.getByText(/Week 3 volume changes from 240 to 180 min/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Discard" })).toBeEnabled();
  });

  it("applies, reports the new workouts and shows the Applied badge", async () => {
    mockFetch(200, { status: "applied", result: { moves: [], warnings: [] }, workouts: [{ id: 3 }] });
    const onApplied = vi.fn();
    render(<ScheduleProposalCard data={data} lang="en" onApplied={onApplied} />);
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(screen.getByText("Applied ✓")).toBeInTheDocument());
    expect(onApplied).toHaveBeenCalledWith([{ id: 3 }]);
    expect(screen.queryByRole("button", { name: "Apply" })).toBeNull();
  });

  it("shows Out of date with the reason on 409", async () => {
    mockFetch(409, { status: "stale", stale_reason: "G2_history" });
    render(<ScheduleProposalCard data={data} lang="en" />);
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(screen.getByText("Out of date")).toBeInTheDocument());
    expect(screen.getByText(/already completed or matched/)).toBeInTheDocument();
  });

  it("keeps the buttons and shows a retry message on failure", async () => {
    mockFetch(500, { detail: "boom" });
    render(<ScheduleProposalCard data={data} lang="en" />);
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(screen.getByText("Couldn't apply — try again.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Apply" })).toBeEnabled();
  });

  it("disables the buttons while applying", async () => {
    let resolve: (r: Response) => void = () => {};
    const pending = new Promise<Response>((r) => { resolve = r; });
    global.fetch = vi.fn().mockImplementation((url: string) =>
      String(url).includes("/proposals/") ? pending : Promise.resolve(new Response("[]", { status: 200 }))
    );
    render(<ScheduleProposalCard data={data} lang="en" />);
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(screen.getByRole("button", { name: "Applying…" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Discard" })).toBeDisabled();
    resolve(new Response(JSON.stringify({ status: "applied", result: {}, workouts: [] }), { status: 200 }));
    await waitFor(() => expect(screen.getByText("Applied ✓")).toBeInTheDocument());
  });

  it("discards", async () => {
    mockFetch(200, { status: "discarded" });
    render(<ScheduleProposalCard data={data} lang="en" />);
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    await waitFor(() => expect(screen.getByText("Discarded")).toBeInTheDocument());
  });

  it("live state overrides the stored card status", () => {
    render(<ScheduleProposalCard data={data} lang="en" liveState={{ status: "applied", result: { warnings: [] } }} />);
    expect(screen.getByText("Applied ✓")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Apply" })).toBeNull();
  });

  it("renders Vietnamese chrome", () => {
    render(<ScheduleProposalCard data={data} lang="vi" />);
    expect(screen.getByRole("button", { name: "Áp dụng" })).toBeInTheDocument();
    expect(screen.getByText(/Tuần 4 · Thứ Hai/)).toBeInTheDocument();
  });

  it("a local Apply wins over a stale 'proposed' liveState from thread load", async () => {
    mockFetch(200, { status: "applied", result: { moves: [], warnings: [] }, workouts: [{ id: 3 }] });
    render(<ScheduleProposalCard data={data} lang="en" liveState={{ status: "proposed" }} />);
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(screen.getByText("Applied ✓")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "Apply" })).toBeNull();
  });

  it("a local Discard wins over a stale 'proposed' liveState from thread load", async () => {
    mockFetch(200, { status: "discarded" });
    render(<ScheduleProposalCard data={data} lang="en" liveState={{ status: "proposed" }} />);
    fireEvent.click(screen.getByRole("button", { name: "Discard" }));
    await waitFor(() => expect(screen.getByText("Discarded")).toBeInTheDocument());
    expect(screen.queryByRole("button", { name: "Apply" })).toBeNull();
  });
});
