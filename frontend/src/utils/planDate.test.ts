import { describe, it, expect } from "vitest";
import { getMondayOfDate, computeCurrentWeek, resolveCurrentWeek } from "./planDate";

describe("planDate utils", () => {
  describe("getMondayOfDate", () => {
    it("returns Monday unchanged when given a Monday", () => {
      // 2026-08-31 is Monday
      const d = new Date(2026, 7, 31);
      const mon = getMondayOfDate(d);
      expect(mon.getFullYear()).toBe(2026);
      expect(mon.getMonth()).toBe(7);
      expect(mon.getDate()).toBe(31);
    });

    it("returns previous Monday when given Tuesday through Sunday", () => {
      // 2026-09-01 is Tuesday -> Aug 31
      expect(getMondayOfDate(new Date(2026, 8, 1)).getDate()).toBe(31);
      // 2026-09-02 is Wednesday -> Aug 31
      expect(getMondayOfDate(new Date(2026, 8, 2)).getDate()).toBe(31);
      // 2026-09-06 is Sunday -> Aug 31
      expect(getMondayOfDate(new Date(2026, 8, 6)).getDate()).toBe(31);
      // 2026-09-07 is Monday -> Sep 7
      expect(getMondayOfDate(new Date(2026, 8, 7)).getDate()).toBe(7);
    });
  });

  describe("computeCurrentWeek", () => {
    it("calculates Week 2 on Tuesday Sep 8 when start_date is Monday Aug 31 (user scenario)", () => {
      const now = new Date(2026, 8, 8, 9, 30); // Sep 8, 2026
      const week = computeCurrentWeek("2026-08-31", 9, null, now);
      expect(week).toBe(2);
    });

    it("calculates Week 1 during the first week (e.g. Sep 3, 2026)", () => {
      const now = new Date(2026, 8, 3, 10, 0); // Sep 3, 2026 (Thursday)
      const week = computeCurrentWeek("2026-08-31", 9, null, now);
      expect(week).toBe(1);
    });

    it("calculates Week 1 on Sunday of week 1 (Sep 6, 2026)", () => {
      const now = new Date(2026, 8, 6, 23, 59); // Sep 6, 2026 (Sunday)
      const week = computeCurrentWeek("2026-08-31", 9, null, now);
      expect(week).toBe(1);
    });

    it("transitions to Week 2 on Monday Sep 7, 2026", () => {
      const now = new Date(2026, 8, 7, 0, 1); // Sep 7, 2026 (Monday)
      const week = computeCurrentWeek("2026-08-31", 9, null, now);
      expect(week).toBe(2);
    });

    it("aligns non-Monday start dates to the Monday of Week 1", () => {
      // User entered Wednesday Sep 2 as start_date; Week 1 Monday is Aug 31
      const now = new Date(2026, 8, 8); // Sep 8 (Tuesday of Week 2)
      const week = computeCurrentWeek("2026-09-02", 9, null, now);
      expect(week).toBe(2);
    });

    it("clamps to Week 1 if today is before the plan start date", () => {
      const now = new Date(2026, 7, 20); // Aug 20 (before Aug 31)
      const week = computeCurrentWeek("2026-08-31", 9, null, now);
      expect(week).toBe(1);
    });

    it("clamps to total_weeks if today is past the end of the plan", () => {
      const now = new Date(2027, 0, 1); // 2027
      const week = computeCurrentWeek("2026-08-31", 9, null, now);
      expect(week).toBe(9);
    });

    it("handles ISO timestamps with timezone offsets", () => {
      const now = new Date(2026, 8, 8);
      const week = computeCurrentWeek("2026-08-31T00:00:00.000Z", 9, null, now);
      expect(week).toBe(2);
    });

    it("falls back to race_date anchoring when start_date is absent", () => {
      // 9 weeks ending on Sunday Nov 1, 2026
      const now = new Date(2026, 8, 8);
      const week = computeCurrentWeek(null, 9, "2026-11-01", now);
      expect(week).toBe(2);
    });

    it("returns 1 for missing or invalid inputs", () => {
      expect(computeCurrentWeek(null, null)).toBe(1);
      expect(computeCurrentWeek(undefined, 0)).toBe(1);
      expect(computeCurrentWeek("invalid-date", 9)).toBe(1);
    });
  });

  describe("resolveCurrentWeek", () => {
    it("returns current week when workouts are generated up to current week", () => {
      const now = new Date(2026, 8, 8); // Sep 8 (Week 2)
      const plan = { start_date: "2026-08-31", total_weeks: 9 };
      const workouts = [
        { week_number: 1 },
        { week_number: 2 },
      ];
      expect(resolveCurrentWeek(plan, workouts, now)).toBe(2);
    });

    it("clamps to maxGeneratedWeek if current week is ahead of generated workouts", () => {
      const now = new Date(2026, 8, 25); // Sep 25 (Week 4)
      const plan = { start_date: "2026-08-31", total_weeks: 9 };
      const workouts = [
        { week_number: 1 },
        { week_number: 2 },
      ];
      // Only Block 1 (weeks 1-2) is generated; clamp to Week 2
      expect(resolveCurrentWeek(plan, workouts, now)).toBe(2);
    });

    it("returns current week if workouts array is empty (e.g. still loading)", () => {
      const now = new Date(2026, 8, 8); // Sep 8 (Week 2)
      const plan = { start_date: "2026-08-31", total_weeks: 9 };
      expect(resolveCurrentWeek(plan, [], now)).toBe(2);
      expect(resolveCurrentWeek(plan, null, now)).toBe(2);
    });

    it("returns 1 if plan is null", () => {
      expect(resolveCurrentWeek(null, [])).toBe(1);
    });
  });
});
