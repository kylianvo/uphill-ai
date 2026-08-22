import type { CoachOverviewAthlete, RunnerLevel } from "../hooks/useCoachOverview";

export interface RosterFilters {
  search: string;
  level: RunnerLevel | "all";
  needsAttentionOnly: boolean;
  raceSearch: string;
}

export function matchesFilters(athlete: CoachOverviewAthlete, filters: RosterFilters): boolean {
  if (filters.search.trim() && !athlete.name.toLowerCase().includes(filters.search.trim().toLowerCase())) {
    return false;
  }
  if (filters.level !== "all" && athlete.runner_level !== filters.level) {
    return false;
  }
  if (filters.needsAttentionOnly && !athlete.needs_attention) {
    return false;
  }
  if (filters.raceSearch.trim()) {
    const raceName = athlete.active_plan?.race_name ?? "";
    if (!raceName.toLowerCase().includes(filters.raceSearch.trim().toLowerCase())) {
      return false;
    }
  }
  return true;
}
