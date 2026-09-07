import { useState } from "react";

export interface PaceZones {
  model?: "4_zone" | "5_zone";
  threshold_pace?: string | null;
  zone1_pace: string;
  zone2_pace: string;
  zone3_pace: string;
  zone4_pace: string;
  zone5_pace?: string;
  zone1_hr: string;
  zone2_hr: string;
  zone3_hr: string;
  zone4_hr: string;
  zone5_hr?: string;
  zone_labels?: Record<string, string>;
  coros_vo2max?: number | null;
  coros_running_level?: number | null;
  custom_pace_zones?: Record<string, unknown> | null;
}

function getBackendUrl(): string {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

export function usePaceZones() {
  const [zones, setZones] = useState<PaceZones | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchPaceZones = async (model?: "4_zone" | "5_zone") => {
    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) return null;
    const url = model
      ? `${getBackendUrl()}/api/auth/pace-zones?model=${model}`
      : `${getBackendUrl()}/api/auth/pace-zones`;
    try {
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setZones(data);
        return data;
      }
    } catch (err) {
      console.error("Failed to load pace zones:", err);
    }
    return null;
  };

  const syncFitness = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("uphill_session_token") : null;
    if (!token) return { success: false, error: "Not authenticated" };
    setLoading(true);
    try {
      const response = await fetch(`${getBackendUrl()}/api/integrations/coros/sync-fitness`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        return { success: false, error: err.detail || "Sync failed" };
      }
      const data = await response.json();
      await fetchPaceZones();
      return { success: true, data };
    } catch (err: unknown) {
      return { success: false, error: err instanceof Error ? err.message : "Network error" };
    } finally {
      setLoading(false);
    }
  };

  return { zones, loading, fetchPaceZones, syncFitness };
}
