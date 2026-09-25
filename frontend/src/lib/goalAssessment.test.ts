import { describe, expect, it } from "vitest";
import { goalPillLabel, missingHints, PlanGoal } from "./goalAssessment";

const goal = (state: PlanGoal["status"]["state"], suggested: number | null = null, hours: number | null = 7 + 40 / 60): PlanGoal => ({
  assessment: null,
  status: { state, suggested_mins: suggested },
  target_time_hours: hours,
});

describe("goalPillLabel", () => {
  it("shows the plan target with on-track status", () => {
    expect(goalPillLabel(goal("on_track"), "en")).toEqual({ text: "Goal 7:40 · On track", dot: "#10b981" });
  });

  it("suggests the new time when ahead or behind", () => {
    expect(goalPillLabel(goal("ahead", 445), "en").text).toBe("Goal 7:40 · Ahead, consider 7:25");
    expect(goalPillLabel(goal("behind", 485), "vi").text).toBe("Mục tiêu 7:40 · Chậm hơn, cân nhắc 8:05");
  });

  it("handles plans without a target or assessment", () => {
    expect(goalPillLabel(goal("no_target", 470, null), "en").text).toBe("Goal · Suggested 7:50");
    expect(goalPillLabel(goal("not_assessed"), "en").text).toBe("Goal 7:40 · Not assessed");
  });
});

describe("missingHints", () => {
  it("maps known keys and drops unknown ones", () => {
    expect(missingHints(["watch", "daily_metrics"], "en")).toEqual(["Connect your watch for recent training"]);
  });
});
