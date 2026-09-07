import { useCallback, useState } from "react";

// Mirrors useDeviceConnection's getBackendUrl -- the app can point at a
// different backend at runtime via ?api=<url> (stored in localStorage as
// UPHILL_API_URL_OVERRIDE), so every hook reads that override rather than
// baking in NEXT_PUBLIC_API_URL alone.
function getBackendUrl(): string {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export type MatchCounts = {
  matched: number;
  suggested: number;
  unmatched: number;
  skipped_manual: number;
};

// Wire shape of GET /api/integrations/matching -- one row per activity, raw
// values only (no pre-formatted strings), so the caller can format them per
// locale. Snake_case, matching the backend's JSON keys exactly; MatchReview
// maps this to its own camelCase MatchItem view model.
export type RawMatchActivity = {
  activity_id: number;
  workout_id: number | null;
  workout_title: string | null;
  distance_km: number | null;
  duration_seconds: number;
  avg_hr: number | null;
  elevation_gain_m: number | null;
  start_time: string;
  match_confidence: number | null;
  match_method: string | null;
  device_model: string | null;
  source_provider: string;
  activity_type?: string | null;
  sets?: number | null;
  quality_score?: number | null;
  quality_grade?: string | null;
  quality_details?: {
    overall_score?: number;
    grade?: string;
    rating?: string;
    subscores?: {
      volume?: number;
      intensity?: number;
      elevation?: number;
    };
    takeaways?: string[];
  } | null;
  match_details?: {
    warmup_distance_km?: number;
    fragments?: number;
    reasons?: string[];
  } | null;
};

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("uphill_session_token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/**
 * Drives the two matching-engine endpoints:
 *   POST  /api/integrations/matching/run              -- run the matcher
 *   PATCH /api/integrations/matching/{activity_id}     -- the athlete's manual correction
 *
 * The matcher runs in shadow mode today (it records decisions, it does not
 * mark workouts complete) and a manual correction is permanent (match_method
 * becomes 'manual' and no automatic run ever touches it again, whether the
 * correction assigns a workout_id or clears one to null) -- see
 * services/matching/runner.py and db.set_manual_match. Those two facts are
 * backend behaviour, not something this hook can change; MatchReview is
 * responsible for saying so to the athlete before they act.
 */
export function useMatching() {
  const [running, setRunning] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  const runMatching = useCallback(
    async (arg?: number | { days?: number; planId?: number | null }): Promise<MatchCounts | null> => {
      const API_BASE_URL = getBackendUrl();
      setRunning(true);
      setError("");
      const days = typeof arg === "number" ? arg : (arg?.days ?? 30);
      const planId = typeof arg === "object" ? arg?.planId : undefined;
      const queryParts = [`days=${days}`];
      if (planId != null) queryParts.push(`plan_id=${planId}`);

      try {
        const res = await fetch(`${API_BASE_URL}/api/integrations/matching/run?${queryParts.join("&")}`, {
          method: "POST",
          headers: authHeaders(),
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body?.detail || "Could not match your activities.");
        return body as MatchCounts;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not match your activities.");
        return null;
      } finally {
        setRunning(false);
      }
    },
    []
  );

  // workout_id travels as a query param (matching the backend's route
  // signature, which reads it that way, not from a JSON body). Omitting the
  // param entirely for a clear (rather than sending workout_id=null as
  // literal text) is deliberate -- the endpoint's default is None either way,
  // and this avoids ever emitting a query string a naive server-side parser
  // could mistake for the literal id "null".
  const patchMatch = useCallback(
    async (activityId: number, workoutId: number | null): Promise<boolean> => {
      const API_BASE_URL = getBackendUrl();
      setError("");
      const query = workoutId === null ? "" : `?workout_id=${workoutId}`;
      try {
        const res = await fetch(`${API_BASE_URL}/api/integrations/matching/${activityId}${query}`, {
          method: "PATCH",
          headers: authHeaders(),
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body?.detail || "Could not update the match.");
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not update the match.");
        return false;
      }
    },
    []
  );

  const confirmMatch = useCallback(
    (activityId: number, workoutId: number) => patchMatch(activityId, workoutId),
    [patchMatch]
  );
  const clearMatch = useCallback(
    (activityId: number) => patchMatch(activityId, null),
    [patchMatch]
  );

  // GET /api/integrations/matching -- lists the caller's activities in the
  // window with their current match state, so the review UI has something
  // to render on load (previously only POST run and PATCH correct existed).
  const fetchMatches = useCallback(
    async (arg?: number | { days?: number; planId?: number | null }): Promise<RawMatchActivity[] | null> => {
      const API_BASE_URL = getBackendUrl();
      setError("");
      const days = typeof arg === "number" ? arg : (arg?.days ?? 30);
      const planId = typeof arg === "object" ? arg?.planId : undefined;
      const queryParts = [`days=${days}`];
      if (planId != null) queryParts.push(`plan_id=${planId}`);

      try {
        const res = await fetch(`${API_BASE_URL}/api/integrations/matching?${queryParts.join("&")}`, {
          method: "GET",
          headers: authHeaders(),
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body?.detail || "Could not load your matches.");
        return (body?.activities ?? []) as RawMatchActivity[];
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load your matches.");
        return null;
      }
    },
    []
  );

  const syncWatch = useCallback(
    async (options?: { days?: number; planId?: number | null }): Promise<boolean> => {
      const API_BASE_URL = getBackendUrl();
      setSyncing(true);
      setError("");
      const days = options?.days ?? 30;
      const planId = options?.planId;
      const queryParts = [`days=${days}`];
      if (planId != null) queryParts.push(`plan_id=${planId}`);

      try {
        const res = await fetch(`${API_BASE_URL}/api/integrations/coros/sync?${queryParts.join("&")}`, {
          method: "POST",
          headers: authHeaders(),
        });
        const body = await res.json();
        if (!res.ok) throw new Error(body?.detail || "Watch sync failed.");
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Watch sync failed.");
        return false;
      } finally {
        setSyncing(false);
      }
    },
    []
  );

  return { running, syncing, error, runMatching, confirmMatch, clearMatch, fetchMatches, syncWatch };
}
