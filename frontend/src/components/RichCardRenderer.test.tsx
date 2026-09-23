import { it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import RichCardRenderer from "./RichCardRenderer";
import { ToolResultEvent } from "../lib/coachChatStream";

const weekResult: ToolResultEvent = {
  type: "tool_result",
  tool_call_id: "call_1",
  name: "get_week",
  status: "success",
  card_type: "week_schedule",
  card_data: {
    week_number: 4,
    total_distance_km: 48.5,
    total_elevation_gain_m: 1650,
    plan_start_date: "2026-08-31",
    race_date: "2026-11-01",
    workouts: [
      {
        id: 101,
        day_of_week: "Tuesday",
        week_number: 4,
        title: "Hill Repeats",
        type: "Interval",
        target_zone: "Zone 4",
        duration_minutes: 45,
        distance_km: 10.0,
        elevation_gain_m: 450,
        description: "6x3min uphill Zone 4",
        approved_at: "2026-01-01T00:00:00Z",
        source: "ai_generated",
        is_completed: false,
        is_missed: false,
      },
    ],
  },
};

const weekReviewResult: ToolResultEvent = {
  type: "tool_result",
  tool_call_id: "call_review",
  name: "week_review",
  status: "success",
  card_type: "week_review",
  card_data: {
    week_number: 4,
    planned: { duration_minutes: 300, distance_km: 45.0, elevation_gain_m: 1500, workout_count: 3 },
    actual: {
      total_actual_km: 40,
      total_actual_minutes: 280,
      total_actual_vert_m: 1420,
      matched_km: 42.0,
      matched_vert_m: 1400,
      matched_count: 2,
      unplanned_km: 0,
      unplanned_hours: 0,
      unplanned_vert_m: 0,
      unplanned_count: 0,
    },
    completion_pct: 93,
    checkbox_completion_pct: 90,
    per_workout: [],
    unplanned: [],
    missed: [],
    coverage: { completed_count: 2, matched_count: 2, checkbox_only_count: 0 },
    narrative: { summary: "Strong week.", highlights: ["Hit every long run on target."], watch: [] },
    week_label: "1 Week Ago (Week 4)",
  },
};

const pacingResult: ToolResultEvent = {
  type: "tool_result",
  tool_call_id: "call_2",
  name: "pace_strategy",
  status: "success",
  card_type: "pacing_splits",
  card_data: {
    race_name: "Dalat Ultra Trail 70K",
    distance_label: "70K",
    total_distance_km: 71.2,
    total_elevation_m: 3150.0,
    target_time_formatted: "12h 45m",
    splits: [
      {
        name: "Start",
        distance_km: 0,
        elevation_m: 1500,
        target_pace: "0:00",
        split_time: "00:00:00",
        cumulative_time_mins: 0,
        flat_equivalent_km: 0,
        grade_pct: 0,
        effort: "run",
      },
      {
        name: "CP1 - Tiger Falls",
        distance_km: 14.2,
        elevation_m: 2120,
        target_pace: "08:15",
        split_time: "01:57:00",
        cumulative_time_mins: 117,
        flat_equivalent_km: 16,
        grade_pct: 5,
        effort: "run",
      },
    ],
  },
};

const knowledgeResult: ToolResultEvent = {
  type: "tool_result",
  tool_call_id: "call_3",
  name: "kb_search",
  status: "success",
  card_type: "knowledge_citations",
  card_data: {
    query: "80/20 intensity",
    citations: [
      {
        topic: "Training",
        chapter_title: "Chapter 6",
        summary: "80/20 intensity distribution keeps most training easy.",
        key_points: [],
        tags: ["Training for the Uphill Athlete"],
        relevance_score: 0.89,
      },
    ],
  },
};

const errorResult: ToolResultEvent = {
  type: "tool_result",
  tool_call_id: "call_4",
  name: "get_week",
  status: "error",
  card_type: null,
  card_data: null,
};

it("renders week_schedule as a real WorkoutCard", () => {
  render(<RichCardRenderer result={weekResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("Hill Repeats")).toBeInTheDocument();
  expect(screen.getByText(/48.5/)).toBeInTheDocument();
});

it("renders week_review with the real WeeklyReview component", () => {
  render(<RichCardRenderer result={weekReviewResult} lang="en" onOpenPaceStrategy={() => {}} />);
  // The wrapper's own header
  expect(screen.getByText("1 Week Ago (Week 4)")).toBeInTheDocument();
  // Proof WeeklyReview itself rendered the fixture: its narrative highlight text,
  // under its own "Highlights" section, is something only WeeklyReview draws.
  expect(screen.getByText("Highlights")).toBeInTheDocument();
  expect(screen.getByText("Hit every long run on target.")).toBeInTheDocument();
});

it("renders pacing_splits with the profile chart, splits table, and an Open in Pace Strategy button", () => {
  render(<RichCardRenderer result={pacingResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("Dalat Ultra Trail 70K")).toBeInTheDocument();
  expect(screen.getByText("Open in Pace Strategy")).toBeInTheDocument();
  expect(screen.getByText("CP1 - Tiger Falls")).toBeInTheDocument();
});

it("fires onOpenPaceStrategy with race name, distance, and distance_label on click", () => {
  const onOpenPaceStrategy = vi.fn();
  render(<RichCardRenderer result={pacingResult} lang="en" onOpenPaceStrategy={onOpenPaceStrategy} />);
  screen.getByText("Open in Pace Strategy").click();
  expect(onOpenPaceStrategy).toHaveBeenCalledWith({
    race_name: "Dalat Ultra Trail 70K",
    distance_km: 71.2,
    distance_label: "70K",
  });
});

it("renders knowledge_citations as real KnowledgeCard components", () => {
  render(<RichCardRenderer result={knowledgeResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("Chapter 6")).toBeInTheDocument();
  expect(screen.getByText(/80\/20 intensity distribution/)).toBeInTheDocument();
});

it("renders nothing (or an inline error note) for a failed tool, never crashing", () => {
  const { container } = render(<RichCardRenderer result={errorResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(container).toBeTruthy();
});

it("omits the D+ elevation segment when total_elevation_m is null", () => {
  const noElevation: ToolResultEvent = {
    ...pacingResult,
    card_data: { ...pacingResult.card_data, total_elevation_m: null },
  };
  render(<RichCardRenderer result={noElevation} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.queryByText(/D\+/)).not.toBeInTheDocument();
});

it("passes target_time_mins through to onOpenPaceStrategy when target_time_hours is present", () => {
  const withTargetTime: ToolResultEvent = {
    ...pacingResult,
    card_data: { ...pacingResult.card_data, target_time_hours: 12.75 },
  };
  const onOpenPaceStrategy = vi.fn();
  render(<RichCardRenderer result={withTargetTime} lang="en" onOpenPaceStrategy={onOpenPaceStrategy} />);
  screen.getByText("Open in Pace Strategy").click();
  expect(onOpenPaceStrategy).toHaveBeenCalledWith(
    expect.objectContaining({ target_time_mins: 12.75 * 60 })
  );
});

it("builds a bilingual week_review header from weeks_ago/target_week when present", () => {
  const withNewFields: ToolResultEvent = {
    ...weekReviewResult,
    card_data: { ...weekReviewResult.card_data, weeks_ago: 2, target_week: 3, week_label: "2 Weeks Ago (Week 3)" },
  };
  render(<RichCardRenderer result={withNewFields} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("2 Weeks Ago (Week 3)")).toBeInTheDocument();
});

it("does not crash and renders nothing for an old-shape week_schedule payload", () => {
  const oldShape: ToolResultEvent = {
    type: "tool_result",
    tool_call_id: "call_old",
    name: "get_week",
    status: "success",
    card_type: "week_schedule",
    card_data: { workouts: [{ day: "Tuesday", name: "Easy" }] },
  };
  const spy = vi.spyOn(console, "error").mockImplementation(() => {});
  expect(() =>
    render(<RichCardRenderer result={oldShape} lang="en" onOpenPaceStrategy={() => {}} />)
  ).not.toThrow();
  expect(screen.queryByText("Easy")).not.toBeInTheDocument();
  spy.mockRestore();
});

it("catches a render throw from a card component via the error boundary and renders nothing", () => {
  const malformed: ToolResultEvent = {
    type: "tool_result",
    tool_call_id: "call_bad",
    name: "week_review",
    status: "success",
    card_type: "week_review",
    // Passes the week_review shape guard (planned/actual objects, per_workout
    // array), but omits `unplanned`, which WeeklyReview reads unconditionally
    // (`unplanned.length`) and would throw on -- proving the boundary still
    // holds even when a shape a guard doesn't check slips through.
    card_data: { planned: {}, actual: {}, per_workout: [] },
  };
  const spy = vi.spyOn(console, "error").mockImplementation(() => {});
  const { container } = render(<RichCardRenderer result={malformed} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(container.firstChild).toBeNull();
  spy.mockRestore();
});

it("renders a schedule_proposal card and ignores a malformed one", () => {
  const good = {
    type: "tool_result" as const, tool_call_id: "p1", name: "propose_schedule_change", status: "success" as const,
    card_type: "schedule_proposal",
    card_data: { proposal_id: 1, operations: [], diff: [], warnings: [], rationale: "r", status: "proposed" },
  };
  const { rerender, container } = render(<RichCardRenderer result={good} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("Proposed schedule change")).toBeInTheDocument();
  rerender(
    <RichCardRenderer result={{ ...good, card_data: { diff: "nope" } }} lang="en" onOpenPaceStrategy={() => {}} />
  );
  expect(container.textContent).toBe("");
});
