import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MatchedActivityCard from "./MatchedActivityCard";
import type { RawMatchActivity } from "../hooks/useMatching";

const activity: RawMatchActivity = {
  activity_id: 1,
  workout_id: 5,
  workout_title: "Easy Run",
  distance_km: 10,
  duration_seconds: 3600,
  avg_hr: 140,
  elevation_gain_m: 50,
  start_time: "2026-10-13T06:00:00Z",
  match_confidence: 0.9,
  match_method: "auto",
  device_model: "COROS APEX PRO",
  source_provider: "coros",
  week_context: {
    done_min: 90,
    planned_min: 370,
    next_key: { day_of_week: "Sunday", title: "Club Long Run", type: "Long Run" },
  },
};

describe("MatchedActivityCard week context", () => {
  it("says where the week stands and what the next key session is", () => {
    render(<MatchedActivityCard activity={activity} lang="en" isMobile={false} />);
    expect(screen.getByTestId("week-context-note")).toHaveTextContent(
      "Week so far: 90 of 370 min. Next key session: Sunday, Club Long Run."
    );
  });

  it("words it in Vietnamese with the Vietnamese weekday", () => {
    render(<MatchedActivityCard activity={activity} lang="vi" isMobile={false} />);
    expect(screen.getByTestId("week-context-note")).toHaveTextContent(
      "Tuần này: 90/370 phút. Buổi quan trọng tiếp theo: Chủ Nhật, Club Long Run."
    );
  });

  it("omits the next-key sentence when nothing key is left, and the note when there is no context", () => {
    const { rerender } = render(
      <MatchedActivityCard
        activity={{ ...activity, week_context: { done_min: 370, planned_min: 370, next_key: null } }}
        lang="en"
        isMobile={false}
      />
    );
    expect(screen.getByTestId("week-context-note")).toHaveTextContent(/^Week so far: 370 of 370 min\.$/);
    rerender(<MatchedActivityCard activity={{ ...activity, week_context: null }} lang="en" isMobile={false} />);
    expect(screen.queryByTestId("week-context-note")).not.toBeInTheDocument();
  });
});
