import { it, expect } from "vitest";
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
    workouts: [{ day: "Tuesday", name: "Hill Repeats", workout_type: "hills", distance_km: 10.0, elevation_gain_m: 450, description: "6x3min uphill Zone 4" }],
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
    total_distance_km: 71.2,
    total_elevation_m: 3150,
    target_time_formatted: "12h 45m",
    splits: [{ name: "CP1 - Tiger Falls", distance_km: 14.2, elevation_m: 620, target_pace: "08:15", split_time: "01:57:00" }],
  },
};

const errorResult: ToolResultEvent = {
  type: "tool_result",
  tool_call_id: "call_3",
  name: "get_week",
  status: "error",
  card_type: null,
  card_data: null,
};

it("renders WeekWorkoutCard for week_schedule", () => {
  render(<RichCardRenderer result={weekResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("Hill Repeats")).toBeInTheDocument();
  expect(screen.getByText(/48.5/)).toBeInTheDocument();
});

it("renders PacingSplitCard with an Open in Pace Strategy button", () => {
  render(<RichCardRenderer result={pacingResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(screen.getByText("Dalat Ultra Trail 70K")).toBeInTheDocument();
  expect(screen.getByText("Open in Pace Strategy")).toBeInTheDocument();
});

it("renders nothing (or an inline error note) for a failed tool, never crashing", () => {
  const { container } = render(<RichCardRenderer result={errorResult} lang="en" onOpenPaceStrategy={() => {}} />);
  expect(container).toBeTruthy();
});
