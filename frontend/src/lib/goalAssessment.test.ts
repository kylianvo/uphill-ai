import { describe, expect, it } from "vitest";
import { Feasibility, feasibilityNotice, GoalPath, pathNotice, goalPillLabel, missingHints, PlanGoal, planSupportNotice } from "./goalAssessment";

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

describe("feasibilityNotice", () => {
  const f = (over: Partial<Feasibility> = {}): Feasibility => ({
    verdict: "unsupported",
    capacity_h: 3.7,
    needed_h: 10.9,
    weeks_needed: null,
    levers: ["more_days", "double_sessions", "shorter_race"],
    confidence: "measured",
    ...over,
  });

  it("says what the week holds against what the goal needs, with the first two levers", () => {
    const en = feasibilityNotice(f(), "en")!;
    expect(en).toContain("about 3.7h; this goal needs about 10.9h");
    expect(en).toContain("More training days would close the gap.");
    expect(en).toContain("Double sessions would help.");
    expect(en).not.toContain("shorter race");
  });

  it("speaks Vietnamese with the technical terms kept in English and no banned words", () => {
    const vi = feasibilityNotice(f({ verdict: "stretch", levers: ["steeper_venue", "fewer_mountain_minimum"] }), "vi")!;
    expect(vi).toContain("Làm được nhưng sát");
    expect(vi).toContain("Long Run");
    expect(vi).not.toMatch(/thể tích|sinh lý|kiến tạo|bảo chứng|tối ưu hóa/);
  });

  it("uses the week count for more_weeks and flags an estimated pace", () => {
    const n = feasibilityNotice(f({ levers: ["more_weeks"], weeks_needed: 18, confidence: "estimated" }), "en")!;
    expect(n).toContain("takes about 18 weeks");
    expect(n).toContain("(pace estimated)");
  });

  it("stays quiet when the goal is supported or there is no verdict", () => {
    expect(feasibilityNotice(f({ verdict: "supported" }), "en")).toBeNull();
    expect(feasibilityNotice(null, "vi")).toBeNull();
    expect(feasibilityNotice(undefined, "en")).toBeNull();
  });
});

describe("pathNotice", () => {
  const p = (over: Partial<GoalPath> = {}): GoalPath => ({
    b: "on", a: "behind", measured_pct: 2.14, expected_pct: 1.5, weeks: 6, confidence: "medium", ...over,
  });

  it("names the B and A status and the measured change, in both languages", () => {
    expect(pathNotice(p(), "en")).toBe("B on track · A behind. Aerobic speed is 2.1% faster than at the start.");
    expect(pathNotice(p({ b: "ahead" }), "vi")).toContain("B vượt lộ trình · A chậm lộ trình");
    expect(pathNotice(p({ measured_pct: -1 }), "en")).toContain("1.0% slower");
  });

  it("flags an early read and stays quiet without data", () => {
    expect(pathNotice(p({ confidence: "low" }), "en")).toContain("(early read)");
    expect(pathNotice(null, "en")).toBeNull();
  });
});
