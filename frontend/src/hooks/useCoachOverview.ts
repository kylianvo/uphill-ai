/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState } from "react";

function getBackendUrl(): string {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export type RunnerLevel = "beginner" | "intermediate" | "advanced" | "elite";

export interface CoachOverviewAthlete {
  athlete_id: number;
  name: string;
  runner_level: RunnerLevel;
  needs_attention: boolean;
  active_plan: {
    plan_id: number;
    race_name: string;
    race_date: string;
    current_week: number;
    total_weeks: number;
  } | null;
  adherence_pct: number | null;
  last_completed: { week_number: number; day_of_week: string } | null;
  missed_streak: number;
}

export interface RaceBreakdownEntry {
  race_name: string;
  race_date: string | null;
  count: number;
  athletes: { athlete_id: number; name: string }[];
}

export interface CoachOverview {
  athletes: CoachOverviewAthlete[];
  action_items: {
    draft_plans: { plan_id: number; athlete_id: number; athlete_name: string; race_name: string }[];
    pending_workout_approvals: { workout_id: number; plan_id: number; athlete_id: number; athlete_name: string; title: string }[];
  };
  phase_alerts: { athlete_id: number; athlete_name: string; phase: string; starts: "this_week" | "next_week" }[];
  workout_type_mix: { type: string; count: number; pct: number }[];
  adherence_trend: { week_number: number; adherence_pct: number }[];
  missed_by_day: { day_of_week: string; count: number }[];
  rpe_distribution: { avg_rpe: number | null; by_value: { rpe: number; count: number }[] };
  race_readiness: { on_track: number; at_risk: number; behind: number };
  roster_totals: { distance_km: number; duration_hours: number; elevation_gain_m: number; workout_count: number };
  most_consistent: { athlete_id: number; name: string; adherence_pct: number }[];
  races: RaceBreakdownEntry[];
  athletes_without_race: number;
}

export function useCoachOverview() {
  const API_BASE_URL = getBackendUrl();

  const [overview, setOverview] = useState<CoachOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState("");

  const authHeaders = () => {
    const token = localStorage.getItem("uphill_session_token");
    return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
  };

  const fetchOverview = async (days?: number, athleteId?: number | null, level?: string | null) => {
    setOverviewLoading(true);
    setOverviewError("");
    try {
      const params = new URLSearchParams();
      if (days) params.set("days", String(days));
      if (athleteId) params.set("athlete_id", String(athleteId));
      if (level && level !== "all") params.set("level", level);
      const queryString = params.toString();
      const url = queryString ? `${API_BASE_URL}/api/coaching/overview?${queryString}` : `${API_BASE_URL}/api/coaching/overview`;
      const res = await fetch(url, { headers: authHeaders() });
      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.detail || "Failed to load overview.");
      }
      setOverview(body);
    } catch (err: any) {
      setOverviewError(err.message || "Failed to load overview.");
      setOverview(null);
    } finally {
      setOverviewLoading(false);
    }
  };

  return { overview, overviewLoading, overviewError, fetchOverview };
}
