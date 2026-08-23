import { describe, it, expect } from "vitest";
import { matchesFilters, type RosterFilters } from "./coachRosterFilters";
import type { CoachOverviewAthlete } from "../hooks/useCoachOverview";

function makeAthlete(overrides: Partial<CoachOverviewAthlete> = {}): CoachOverviewAthlete {
  return {
    athlete_id: 1,
    name: "Jane Runner",
    runner_level: "advanced",
    needs_attention: false,
    active_plan: {
      plan_id: 1,
      race_name: "VMM 70km",
      race_date: "2026-11-15",
      current_week: 9,
      total_weeks: 16,
    },
    adherence_pct: 0.8,
    last_completed: { week_number: 9, day_of_week: "Monday" },
    missed_streak: 0,
    ...overrides,
  };
}

const NO_FILTERS: RosterFilters = { search: "", level: "all", needsAttentionOnly: false, raceSearch: "" };

describe("matchesFilters", () => {
  it("matches everything when all filters are empty/default", () => {
    expect(matchesFilters(makeAthlete(), NO_FILTERS)).toBe(true);
  });

  it("name search matches case-insensitively", () => {
    expect(matchesFilters(makeAthlete({ name: "Jane Runner" }), { ...NO_FILTERS, search: "jane" })).toBe(true);
    expect(matchesFilters(makeAthlete({ name: "Jane Runner" }), { ...NO_FILTERS, search: "bob" })).toBe(false);
  });

  it("level filter matches only the selected level", () => {
    const athlete = makeAthlete({ runner_level: "elite" });
    expect(matchesFilters(athlete, { ...NO_FILTERS, level: "elite" })).toBe(true);
    expect(matchesFilters(athlete, { ...NO_FILTERS, level: "beginner" })).toBe(false);
    expect(matchesFilters(athlete, { ...NO_FILTERS, level: "all" })).toBe(true);
  });

  it("needsAttentionOnly excludes athletes with needs_attention=false", () => {
    expect(matchesFilters(makeAthlete({ needs_attention: false }), { ...NO_FILTERS, needsAttentionOnly: true })).toBe(false);
    expect(matchesFilters(makeAthlete({ needs_attention: true }), { ...NO_FILTERS, needsAttentionOnly: true })).toBe(true);
  });

  it("race search matches active_plan.race_name case-insensitively", () => {
    const athlete = makeAthlete({
      active_plan: {
        plan_id: 1,
        race_name: "Fansipan Trail",
        race_date: "2027-01-01",
        current_week: 1,
        total_weeks: 10,
      },
    });
    expect(matchesFilters(athlete, { ...NO_FILTERS, raceSearch: "fansipan" })).toBe(true);
    expect(matchesFilters(athlete, { ...NO_FILTERS, raceSearch: "vmm" })).toBe(false);
  });

  it("race search excludes athletes with no active plan when a race search is set", () => {
    const athlete = makeAthlete({ active_plan: null });
    expect(matchesFilters(athlete, { ...NO_FILTERS, raceSearch: "vmm" })).toBe(false);
    expect(matchesFilters(athlete, NO_FILTERS)).toBe(true); // empty race search doesn't exclude no-plan athletes
  });

  it("combines all filters with AND", () => {
    const athlete = makeAthlete({
      name: "Alex Chen",
      runner_level: "elite",
      needs_attention: true,
      active_plan: {
        plan_id: 2,
        race_name: "Fansipan Trail",
        race_date: "2027-01-01",
        current_week: 1,
        total_weeks: 10,
      },
    });
    expect(
      matchesFilters(athlete, {
        search: "alex",
        level: "elite",
        needsAttentionOnly: true,
        raceSearch: "fansipan",
      })
    ).toBe(true);
    expect(
      matchesFilters(athlete, {
        search: "alex",
        level: "beginner",
        needsAttentionOnly: true,
        raceSearch: "fansipan",
      })
    ).toBe(false);
  });
});
