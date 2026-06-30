/* eslint-disable @typescript-eslint/no-explicit-any */
import { useState, useEffect } from "react";
import { WorkoutInfo, getWorkoutInfo as staticLookup } from "../data/workoutLibrary";

export interface WorkoutTypeEntry {
  type_key: string;
  display_name: string;
  zone: string;
  color: string;
  overview: string;
  execution: string;
  benefit: string;
  warning: string;
  lang: string;
}

// Singleton cache so repeated renders don't re-fetch
let cache: WorkoutTypeEntry[] | null = null;
let fetchPromise: Promise<WorkoutTypeEntry[]> | null = null;

async function fetchTypes(apiBase: string, lang: string): Promise<WorkoutTypeEntry[]> {
  if (cache) return cache;
  if (fetchPromise) return fetchPromise;

  fetchPromise = fetch(`${apiBase}/api/workouts/types?lang=${lang}`)
    .then((r) => (r.ok ? r.json() : { types: [] }))
    .then((data) => {
      cache = data.types || [];
      return cache as WorkoutTypeEntry[];
    })
    .catch(() => {
      return [] as WorkoutTypeEntry[];
    });

  return fetchPromise;
}

export function useWorkoutTypes(lang: string = "en") {
  const [types, setTypes] = useState<WorkoutTypeEntry[]>(cache || []);
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    fetchTypes(API_BASE, lang).then((t) => {
      if (t.length > 0) setTypes(t);
    });
  }, [API_BASE, lang]);

  return types;
}

// Maps backend `type` values to DB type_keys
const DB_TYPE_MAP: Record<string, string> = {
  "easy":               "easy_run",
  "long run":           "long_run",
  "tempo":              "tempo_run",
  "threshold":          "tempo_run",
  "interval":           "interval",
  "muscular endurance": "me_session",
  "strength":           "strength",
  "recovery":           "recovery_run",
  "active recovery":    "recovery_run",
  "cross-training":     "cross_training",
  "aerobic capacity":   "easy_run",
  "walk/run":           "easy_run",
  "race":               "rest",
  "rest":               "rest",
};

/** Resolve workout info: DB-sourced first, static fallback second. */
export function resolveWorkoutInfo(
  title: string,
  type: string,
  dbTypes: WorkoutTypeEntry[]
): WorkoutInfo | null {
  if (dbTypes.length > 0) {
    // 1. Direct type → type_key mapping (most reliable)
    const mappedKey = DB_TYPE_MAP[type.toLowerCase()];
    const match = mappedKey
      ? dbTypes.find((t) => t.type_key === mappedKey)
      // 2. Keyword fallback on title + type
      : dbTypes.find((t) => `${title} ${type}`.toLowerCase().includes(t.type_key.replace(/_/g, " ")));
    if (match) {
      return {
        zone: match.zone as any,
        color: match.color,
        overview: match.overview,
        execution: match.execution,
        benefit: match.benefit,
        warning: match.warning,
      };
    }
  }
  // Fallback to static library
  return staticLookup(title, type);
}

/** Invalidate cache — call after triggering a re-extraction. */
export function invalidateWorkoutTypesCache() {
  cache = null;
  fetchPromise = null;
}
