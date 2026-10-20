import { describe, expect, it } from "vitest";
import { goalPillLabel, missingHints, PlanGoal, planSupportNotice } from "./goalAssessment";

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


describe("planSupportNotice", () => {
  const base = { goals: { a: 819, b: 870, c: 960 }, goals_unadjusted: { a: 810, b: 855, c: 945 } };
  const support = (over = {}) => ({
    a_supported: false,
    shortfall_pct: 1.2,
    improvement_assumed_pct: 2.75,
    improvement_supported_pct: 1.5,
    weeks_assumed: 11,
    weeks_supported: 6,
    problem_weeks: {},
    reasons: [],
    ...over,
  });
  const a = (over = {}) => ({ ...base, plan_support: support(over) }) as unknown as import("./goalAssessment").GoalAssessment;

  it("says how much the plan delivers and how far the goals moved, in English and Vietnamese", () => {
    expect(planSupportNotice(a(), "en")).toContain("delivers 1.5% of the 2.8% improvement");
    expect(planSupportNotice(a(), "en")).toContain("moved 1.2% later");
    expect(planSupportNotice(a(), "vi")).toContain("Plan chưa đỡ hết mục tiêu A");
    expect(planSupportNotice(a(), "vi")).toContain("lùi 1.2%");
  });

  it("stays quiet when the plan backs the A goal or there is nothing to compare", () => {
    expect(planSupportNotice(a({ a_supported: true, shortfall_pct: 0 }), "en")).toBeNull();
    expect(planSupportNotice(null, "en")).toBeNull();
    expect(planSupportNotice({ goals: base.goals } as never, "en")).toBeNull();
  });
});
