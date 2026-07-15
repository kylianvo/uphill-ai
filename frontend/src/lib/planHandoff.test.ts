import { describe, it, expect } from "vitest";
import { minsToHms, isTaperPhase, buildPaceHandoffFromPlan } from "./planHandoff";

describe("minsToHms", () => {
  it("splits whole minutes into h/m/s strings", () => {
    expect(minsToHms(272)).toEqual({ h: "4", m: "32", s: "0" });
  });

  it("carries fractional minutes into seconds", () => {
    expect(minsToHms(90.5)).toEqual({ h: "1", m: "30", s: "30" });
  });

  it("handles sub-hour durations", () => {
    expect(minsToHms(45)).toEqual({ h: "0", m: "45", s: "0" });
  });
});

describe("isTaperPhase", () => {
  it("matches phase strings containing 'taper' case-insensitively", () => {
    expect(isTaperPhase("Taper")).toBe(true);
    expect(isTaperPhase("taper")).toBe(true);
    expect(isTaperPhase("Taper Week")).toBe(true);
  });

  it("returns false for other phases and empty input", () => {
    expect(isTaperPhase("Base")).toBe(false);
    expect(isTaperPhase("")).toBe(false);
    expect(isTaperPhase(null)).toBe(false);
    expect(isTaperPhase(undefined)).toBe(false);
  });
});

describe("buildPaceHandoffFromPlan", () => {
  it("includes distance and target time for a goal_type=time plan", () => {
    const result = buildPaceHandoffFromPlan({
      race_name: "UTA100",
      goal_type: "time",
      course_distance_km: 100,
      target_time_hours: 20.5,
    });
    expect(result).toEqual({
      race_name: "UTA100",
      distance_km: 100,
      target_time_mins: 1230,
    });
  });

  it("omits target_time_mins for non-time goal types", () => {
    const result = buildPaceHandoffFromPlan({
      race_name: "SUM30",
      goal_type: "finish",
      course_distance_km: 30,
      target_time_hours: undefined,
    });
    expect(result).toEqual({ race_name: "SUM30", distance_km: 30 });
  });

  it("omits distance_km when not present on the plan", () => {
    const result = buildPaceHandoffFromPlan({
      race_name: "My First Marathon",
      goal_type: "finish",
      course_distance_km: null,
      target_time_hours: null,
    });
    expect(result).toEqual({ race_name: "My First Marathon" });
  });
});
