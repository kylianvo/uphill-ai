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
    narrative: { summary: "Strong week.", highlights: [], watch: [] },
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
  expect(screen.getByText("1 Week Ago (Week 4)")).toBeInTheDocument();
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
