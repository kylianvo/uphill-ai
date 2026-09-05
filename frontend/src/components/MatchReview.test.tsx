import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MatchReview, { type MatchItem } from "./MatchReview";

// useMatching is this task's own hook, reviewed and covered separately in
// useMatching.test.ts. Replacing it here with a stateful fake keeps this
// suite focused on what MatchReview renders and which payload it sends, not
// on re-testing the hook's fetch plumbing.
const mockUseMatching = vi.fn();
vi.mock("../hooks/useMatching", () => ({
  useMatching: (...args: unknown[]) => mockUseMatching(...args),
}));

// MatchReview reads `lang` from AppContext, the same source ConnectedAccounts
// and ProfileSettingsModal use.
const mockUseAppContext = vi.fn();
vi.mock("../contexts/AppContext", () => ({
  useAppContext: (...args: unknown[]) => mockUseAppContext(...args),
}));

function baseHook(overrides: Record<string, unknown> = {}) {
  return {
    running: false,
    error: "",
    runMatching: vi.fn(async () => ({ matched: 0, suggested: 0, unmatched: 0, skipped_manual: 0 })),
    confirmMatch: vi.fn(async () => true),
    clearMatch: vi.fn(async () => true),
    ...overrides,
  };
}

const suggestItem: MatchItem = {
  activityId: 7,
  workoutId: 42,
  workoutTitle: "Tuesday hill repeats",
  activitySummary: "8.2 km, 42:10, avg HR 151",
  activityDate: "Sep 2",
  confidence: 0.68,
  confidenceBand: "suggest",
  reasons: ["similar distance and duration"],
  deviceModel: "COROS APEX 2 Pro",
  provider: "coros",
};

const autoItem: MatchItem = {
  activityId: 8,
  workoutId: 43,
  workoutTitle: "Wednesday easy run",
  activitySummary: "6.0 km, 30:00, avg HR 138",
  activityDate: "Sep 3",
  confidence: 0.91,
  confidenceBand: "auto",
  reasons: ["distance, duration and date all match"],
  deviceModel: "COROS PACE 3",
  provider: "coros",
};

const unmatchedItem: MatchItem = {
  activityId: 9,
  workoutId: null,
  workoutTitle: null,
  activitySummary: "3.1 km, 15:40, avg HR 160",
  activityDate: "Sep 4",
  confidence: 0,
  confidenceBand: "unmatched",
  reasons: ["no workout scored high enough"],
  deviceModel: null,
  provider: "coros",
};

describe("MatchReview", () => {
  beforeEach(() => {
    mockUseMatching.mockReset();
    mockUseAppContext.mockReset();
    mockUseAppContext.mockReturnValue({ lang: "en" });
    mockUseMatching.mockReturnValue(baseHook());
  });

  it("shows the empty state and says what to do about it", () => {
    render(<MatchReview items={[]} />);
    expect(
      screen.getByText(/No activities to review yet\. Run a check/)
    ).toBeInTheDocument();
  });

  it("renders a populated list across all three confidence bands", () => {
    render(<MatchReview items={[suggestItem, autoItem, unmatchedItem]} />);
    expect(screen.getByText("Needs your confirmation")).toBeInTheDocument();
    expect(screen.getByText("Tuesday hill repeats")).toBeInTheDocument();
    expect(screen.getByText("Matched automatically")).toBeInTheDocument();
    expect(screen.getByText("Wednesday easy run")).toBeInTheDocument();
    expect(screen.getByText("No match found")).toBeInTheDocument();
    expect(screen.getByText("3.1 km, 15:40, avg HR 160")).toBeInTheDocument();
  });

  it("never renders a fabricated confidence percentage for an unmatched activity", () => {
    render(<MatchReview items={[unmatchedItem]} />);
    expect(screen.getByText("No match")).toBeInTheDocument();
    expect(screen.queryByText(/% confidence/)).not.toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("renders COROS attribution with the real per-activity device model next to that activity's data", () => {
    render(<MatchReview items={[suggestItem]} />);
    expect(screen.getByText("8.2 km, 42:10, avg HR 151")).toBeInTheDocument();
    expect(screen.getByText("Data provided by COROS · COROS APEX 2 Pro")).toBeInTheDocument();
  });

  it("renders attribution without a device model when an activity genuinely has none, never fabricating one", () => {
    render(<MatchReview items={[unmatchedItem]} />);
    expect(screen.getByText("Data provided by COROS")).toBeInTheDocument();
    expect(screen.queryByText(/Data provided by COROS ·/)).not.toBeInTheDocument();
  });

  it("confirms a suggested match by calling confirmMatch with the activity and workout ids", async () => {
    const user = userEvent.setup();
    const confirmMatch = vi.fn(async () => true);
    mockUseMatching.mockReturnValue(baseHook({ confirmMatch }));
    render(<MatchReview items={[suggestItem]} />);
    await user.click(screen.getByRole("button", { name: "Yes, that's it" }));
    expect(confirmMatch).toHaveBeenCalledWith(7, 42);
    await waitFor(() => expect(screen.getByText("Saved")).toBeInTheDocument());
  });

  it("clears a match by calling clearMatch with just the activity id", async () => {
    const user = userEvent.setup();
    const clearMatch = vi.fn(async () => true);
    mockUseMatching.mockReturnValue(baseHook({ clearMatch }));
    render(<MatchReview items={[suggestItem]} />);
    await user.click(screen.getByRole("button", { name: "Not this one" }));
    expect(clearMatch).toHaveBeenCalledWith(7);
    await waitFor(() => expect(screen.getByText("Saved")).toBeInTheDocument());
  });

  it("shows a mid-action saving state while a correction is in flight", async () => {
    const user = userEvent.setup();
    let resolvePromise: (v: boolean) => void = () => {};
    const confirmMatch = vi.fn(
      () => new Promise<boolean>((resolve) => { resolvePromise = resolve; })
    );
    mockUseMatching.mockReturnValue(baseHook({ confirmMatch }));
    render(<MatchReview items={[suggestItem]} />);
    await user.click(screen.getByRole("button", { name: "Yes, that's it" }));
    expect(await screen.findByRole("button", { name: "Saving..." })).toBeInTheDocument();
    resolvePromise(true);
    await waitFor(() => expect(screen.getByText("Saved")).toBeInTheDocument());
  });

  it("treats a 404 from a correction as a normal error, not a crash, and keeps the card actionable", async () => {
    const user = userEvent.setup();
    const confirmMatch = vi.fn(async () => false);
    mockUseMatching.mockReturnValue(baseHook({ confirmMatch, error: "Activity not found." }));
    render(<MatchReview items={[suggestItem]} />);
    await user.click(screen.getByRole("button", { name: "Yes, that's it" }));
    expect(screen.getByText("Activity not found.")).toBeInTheDocument();
    expect(screen.queryByText("Saved")).not.toBeInTheDocument();
  });

  it("does not offer a confirm action for an already auto-matched activity, only a correction", () => {
    render(<MatchReview items={[autoItem]} />);
    expect(screen.queryByRole("button", { name: "Yes, that's it" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Not this one" })).toBeInTheDocument();
  });

  it("says reviewing does not complete the workout yet (shadow mode)", () => {
    render(<MatchReview items={[]} />);
    expect(
      screen.getByText(/does not mark the workout complete yet/)
    ).toBeInTheDocument();
  });

  it("makes the permanence of a manual correction clear before the athlete commits", () => {
    render(<MatchReview items={[suggestItem]} />);
    expect(
      screen.getByText(/This is permanent\. Automatic re-checks will never change it/)
    ).toBeInTheDocument();
  });

  it("shows a loading skeleton shaped like the final layout while a run is in progress", () => {
    mockUseMatching.mockReturnValue(baseHook({ running: true }));
    const { container } = render(<MatchReview items={[suggestItem]} />);
    expect(container.querySelectorAll(".match-card-skeleton").length).toBeGreaterThan(0);
    // The real card content must not show through the skeleton.
    expect(screen.queryByText("Tuesday hill repeats")).not.toBeInTheDocument();
  });

  it("surfaces a run error", () => {
    mockUseMatching.mockReturnValue(baseHook({ error: "Could not match your activities." }));
    render(<MatchReview items={[]} />);
    expect(screen.getByText("Could not match your activities.")).toBeInTheDocument();
  });

  it("runs the matcher when Re-check my runs is clicked", async () => {
    const user = userEvent.setup();
    const runMatching = vi.fn(async () => ({ matched: 2, suggested: 1, unmatched: 0, skipped_manual: 0 }));
    mockUseMatching.mockReturnValue(baseHook({ runMatching }));
    render(<MatchReview items={[]} />);
    await user.click(screen.getByRole("button", { name: /Re-check my runs/ }));
    expect(runMatching).toHaveBeenCalledWith(30);
    expect(await screen.findByText(/2 matched automatically, 1 need your confirmation, 0 without a match\./)).toBeInTheDocument();
  });

  it("renders Vietnamese copy, not English, when lang is vi", () => {
    mockUseAppContext.mockReturnValue({ lang: "vi" });
    render(<MatchReview items={[suggestItem, unmatchedItem]} />);
    expect(screen.getByText("Khớp hoạt động")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Kiểm tra lại/ })).toBeInTheDocument();
    expect(screen.getByText("Cần bạn xác nhận")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Đúng rồi" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Không đúng" })).toBeInTheDocument();
    expect(
      screen.getByText(/chưa đánh dấu buổi tập là hoàn thành/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Điều này là vĩnh viễn/)
    ).toBeInTheDocument();
    expect(screen.getByText("Không tìm thấy khớp")).toBeInTheDocument();
    // English copy must not leak through.
    expect(screen.queryByText("Activity matching")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Yes, that's it" })).not.toBeInTheDocument();
  });

  it("translates a known hook error message to Vietnamese when lang is vi", () => {
    mockUseAppContext.mockReturnValue({ lang: "vi" });
    mockUseMatching.mockReturnValue(baseHook({ error: "Activity not found." }));
    render(<MatchReview items={[]} />);
    expect(screen.getByText("Không tìm thấy hoạt động này.")).toBeInTheDocument();
    expect(screen.queryByText("Activity not found.")).not.toBeInTheDocument();
  });
});
