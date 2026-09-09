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
  "race":               "race_day",
  "rest":               "rest",
};

// Types where the coach has already declared the session is NOT hard. For these the
// title may not escalate intensity: a generated title is a label describing STRUCTURE,
// not a prescription. "Progressive Walk-Jog Intervals" is an easy session made of
// repeated bouts — letting `interval` win off that substring painted a beginner's
// walk-jog red and labelled it Zone 4-5, the most dangerous possible mislabel.
// Compound sessions that genuinely are hard (e.g. type "tempo", title
// "Aerobic Base + Interval Sprints") are unaffected — "tempo" isn't in this set.
const NON_ESCALATING_TYPES = new Set([
  "easy",
  "recovery",
  "active recovery",
  "long run",
  "walk/run",
  "rest",
]);

/** Resolve workout info: DB-sourced first, static fallback second. */
export function resolveWorkoutInfo(
  title: string,
  type: string,
  dbTypes: WorkoutTypeEntry[]
): WorkoutInfo | null {
  const typeLower = type.toLowerCase();
  const titleMayEscalate = !NON_ESCALATING_TYPES.has(typeLower);

  if (dbTypes.length > 0) {
    // 1. Title keyword scan first — catches compound sessions like "Aerobic Base + Hill Sprints",
    //    but only for types that haven't already declared themselves easy (see above).
    const titleLower = title.toLowerCase();
    const titleMatch = titleMayEscalate
      ? dbTypes.find((t) => t.type_key.length > 5 && titleLower.includes(t.type_key.replace(/_/g, " ")))
      : undefined;
    // 3's haystack drops the title for non-escalating types too — otherwise the title
    // sneaks back in through the combined string and undoes the guard above.
    const haystack = (titleMayEscalate ? `${titleLower} ${typeLower}` : typeLower);
    const match =
      titleMatch ||
      // 2. Direct type → type_key mapping
      dbTypes.find((t) => t.type_key === DB_TYPE_MAP[typeLower]) ||
      // 3. Combined title+type keyword fallback
      dbTypes.find((t) => haystack.includes(t.type_key.replace(/_/g, " ")));
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
