/* eslint-disable @typescript-eslint/no-explicit-any */
/** Pure helpers behind the plan summary carousel and the weekly volume card. */

export interface WeekVolume {
  week: number;
  km: number;
  mins: number;
  hours: number;
  gainM: number;
  generated: boolean;
}

/** Weekly km / minutes / hours for a list of workouts (same math the Weekly Volume card uses). */
export function weekVolume(weekWorkouts: any[]): { km: number; mins: number; hours: number; gainM: number } {
  const km = weekWorkouts.reduce((sum: number, wo: any) => sum + (wo.distance_km || 0), 0);
  const mins = weekWorkouts.reduce((sum: number, wo: any) => sum + (wo.duration_minutes || 0), 0);
  const gainM = weekWorkouts.reduce((sum: number, wo: any) => sum + (wo.elevation_gain_m || 0), 0);
  return { km, mins, hours: parseFloat((mins / 60).toFixed(1)), gainM };
}

/** One entry per plan week; weeks with no workouts are marked not generated. */
export function planWeeklyVolumes(workouts: any[], totalWeeks: number): WeekVolume[] {
  const byWeek = new Map<number, any[]>();
  for (const wo of workouts) {
    const w = wo.week_number;
    if (!w) continue;
    if (!byWeek.has(w)) byWeek.set(w, []);
    byWeek.get(w)!.push(wo);
  }
  const maxWeek = Math.max(totalWeeks || 0, ...byWeek.keys(), 0);
  return Array.from({ length: maxWeek }, (_, i) => {
    const week = i + 1;
    const wos = byWeek.get(week);
    if (!wos) return { week, km: 0, mins: 0, hours: 0, gainM: 0, generated: false };
    return { week, ...weekVolume(wos), generated: true };
  });
}

/** Whole local-calendar days from today to the race; null when unknown or past. */
export function daysToRace(raceDate: string | null | undefined, now: Date = new Date()): number | null {
  if (!raceDate) return null;
  const p = raceDate.split("-").map((x) => parseInt(x, 10));
  if (p.length < 3 || p.some(Number.isNaN)) return null;
  const race = new Date(p[0], p[1] - 1, p[2]);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const days = Math.round((race.getTime() - today.getTime()) / 86400000);
  return days < 0 ? null : Math.max(0, days);
}

export type DayState = "done" | "missed" | "planned" | "rest";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

/** Mon-Sun state for one week's workouts. */
export function weekDayStates(weekWorkouts: any[]): { day: string; state: DayState }[] {
  return DAYS.map((day) => {
    const wos = weekWorkouts.filter((w: any) => (w.day_of_week || "Monday") === day);
    const active = wos.filter((w: any) => w.type !== "Rest" && w.duration_minutes !== 0);
    let state: DayState = "planned";
    if (active.length === 0) state = "rest";
    else if (active.every((w: any) => w.is_completed === 1)) state = "done";
    else if (active.some((w: any) => w.is_missed === 1)) state = "missed";
    return { day, state };
  });
}
