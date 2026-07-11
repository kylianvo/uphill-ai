import { useEffect, useState } from "react";

export interface RaceMatch {
  race_name: string;
  distance_label: string | null;
  distance_km: number | null;
  elevation_gain_m: number | null;
  terrain: string[];
}

function getBackendUrl(): string {
  if (typeof window !== "undefined") {
    const override = localStorage.getItem("UPHILL_API_URL_OVERRIDE");
    if (override) return override;
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

const MIN_NAME_LENGTH = 3;
const DEBOUNCE_MS = 500;

export function useRaceMatch(
  name: string,
  options?: { distanceKm?: number | string; distanceLabel?: string }
): RaceMatch | null {
  const [match, setMatch] = useState<RaceMatch | null>(null);
  const distanceKm = options?.distanceKm;
  const distanceLabel = options?.distanceLabel;

  useEffect(() => {
    const trimmed = name.trim();
    if (trimmed.length < MIN_NAME_LENGTH) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setMatch(null);
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(() => {
      const params = new URLSearchParams({ name: trimmed });
      if (distanceKm !== undefined && distanceKm !== "" && distanceKm !== null) {
        params.set("distance_km", String(distanceKm));
      }
      if (distanceLabel) {
        params.set("distance_label", distanceLabel);
      }
      fetch(`${getBackendUrl()}/api/kb/match-race?${params.toString()}`, { signal: controller.signal })
        .then((r) => (r.ok ? r.json() : { matched: false }))
        .then((data) => setMatch(data.matched ? (data as RaceMatch & { matched: true }) : null))
        .catch(() => {});
    }, DEBOUNCE_MS);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [name, distanceKm, distanceLabel]);

  return match;
}
