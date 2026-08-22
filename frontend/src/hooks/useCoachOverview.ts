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
  adherence_pct_14d: number | null;
  last_completed: { week_number: number; day_of_week: string } | null;
  missed_streak: number;
}

export interface CoachOverview {
  athletes: CoachOverviewAthlete[];
  action_items: {
    draft_plans: { plan_id: number; athlete_id: number; athlete_name: string; race_name: string }[];
    pending_workout_approvals: { workout_id: number; plan_id: number; athlete_id: number; athlete_name: string; title: string }[];
  };
  phase_alerts: { athlete_id: number; athlete_name: string; phase: string; starts: "this_week" | "next_week" }[];
  workout_type_mix: { type: string; count: number; pct: number }[];
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

  const fetchOverview = async () => {
    setOverviewLoading(true);
    setOverviewError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/coaching/overview`, { headers: authHeaders() });
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
