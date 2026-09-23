/**
 * Utility functions for calendar-derived plan week calculations.
 * Training weeks run Monday to Sunday.
 */

/**
 * Aligns a Date to the Monday of its calendar week (midnight).
 */
export function getMondayOfDate(d: Date): Date {
  const day = d.getDay(); // 0 is Sunday, 1 is Monday, ..., 6 is Saturday
  const offset = day === 0 ? 6 : day - 1;
  const monday = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  monday.setDate(monday.getDate() - offset);
  monday.setHours(0, 0, 0, 0);
  return monday;
}

/**
 * Computes the calendar-derived current week of a plan based on start_date and total_weeks.
 * Clamped between 1 and total_weeks.
 * If the plan start date is in the future, returns 1.
 * If the plan has completed, returns total_weeks.
 */
export function computeCurrentWeek(
  startDateStr?: string | null,
  totalWeeks?: number | null,
  raceDateStr?: string | null,
  now: Date = new Date()
): number {
  if (!totalWeeks || totalWeeks < 1) return 1;

  let startMonday: Date | null = null;

  if (startDateStr) {
    const cleanStr = startDateStr.slice(0, 10);
    const parts = cleanStr.split("-").map(Number);
    if (parts.length === 3 && parts.every((n) => !isNaN(n))) {
      const parsed = new Date(parts[0], parts[1] - 1, parts[2]);
      if (!isNaN(parsed.getTime())) {
        startMonday = getMondayOfDate(parsed);
      }
    }
  }

  // Fallback: anchor backward from race_date if start_date is not set
  if (!startMonday && raceDateStr) {
    const cleanStr = raceDateStr.slice(0, 10);
    const parts = cleanStr.split("-").map(Number);
    if (parts.length === 3 && parts.every((n) => !isNaN(n))) {
      const raceDate = new Date(parts[0], parts[1] - 1, parts[2]);
      if (!isNaN(raceDate.getTime())) {
        const raceMonday = getMondayOfDate(raceDate);
        startMonday = new Date(raceMonday);
        startMonday.setDate(raceMonday.getDate() - (totalWeeks - 1) * 7);
      }
    }
  }

  if (!startMonday) return 1;

  // Use Date.UTC to guarantee timezone- and DST-independent day arithmetic
  const startUtc = Date.UTC(startMonday.getFullYear(), startMonday.getMonth(), startMonday.getDate());
  const todayUtc = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const diffDays = Math.floor((todayUtc - startUtc) / 86400000);
  const week = Math.floor(diffDays / 7) + 1;

  return Math.max(1, Math.min(week, totalWeeks));
}

const WORKOUT_DAY_OFFSETS: Record<string, number> = {
  Monday: 0,
  Tuesday: 1,
  Wednesday: 2,
  Thursday: 3,
  Friday: 4,
  Saturday: 5,
  Sunday: 6,
};

/**
 * Computes the real calendar Date a workout falls on, or null if it can't be
 * computed (no start_date/race_date, or malformed dates). Training weeks run
 * Monday to Sunday: week 1 starts on the Monday on/before plan.start_date, or,
 * falling back to the legacy race_date anchor, on the Monday (raceWeek - 1)
 * weeks before the Monday of race_date's week.
 */
export function computeWorkoutDate(
  plan: { start_date?: string | null; race_date?: string | null; total_weeks?: number | null },
  workouts: Array<{ title: string; type: string; week_number: number }>,
  wo: { day_of_week: string; week_number: number }
): Date | null {
  try {
    let startMonday: Date;

    // Prefer plan_start_date (exact user-inputted date) if stored
    if (plan.start_date) {
      const parts = plan.start_date.split("-");
      const sd = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
      // Week 1 starts on the Monday on or before the start date
      startMonday = getMondayOfDate(sd);
    } else if (plan.race_date) {
      // Fallback: anchor from race date backward (legacy behaviour)
      const parts = plan.race_date.split("-");
      if (parts.length !== 3) return null;
      const raceDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
      const raceWo = workouts.find((w) => {
        const title = w.title.toUpperCase();
        const type = w.type.toUpperCase();
        return title.includes("TARGET EVENT") || type === "RACE";
      });
      const raceWeek = raceWo ? raceWo.week_number : plan.total_weeks;
      if (!raceWeek) return null;
      const raceWeekMonday = getMondayOfDate(raceDate);
      startMonday = new Date(raceWeekMonday);
      startMonday.setDate(raceWeekMonday.getDate() - (raceWeek - 1) * 7);
    } else {
      return null;
    }

    const workoutDayOffset = WORKOUT_DAY_OFFSETS[wo.day_of_week] ?? 0;
    const workoutDate = new Date(startMonday);
    workoutDate.setDate(startMonday.getDate() + (wo.week_number - 1) * 7 + workoutDayOffset);

    return workoutDate;
  } catch (e) {
    console.error(e);
    return null;
  }
}

/**
 * Resolves the week number that should be selected by default when viewing the plan.
 * Takes the calendar-derived current week, clamped to maxGeneratedWeek if workouts
 * are currently only generated for a subset of weeks (e.g. Block 1).
 */
export function resolveCurrentWeek(
  plan?: { start_date?: string | null; total_weeks?: number | null; race_date?: string | null } | null,
  workouts?: Array<{ week_number?: number }> | null,
  now: Date = new Date()
): number {
  if (!plan) return 1;
  const currentWeek = computeCurrentWeek(plan.start_date, plan.total_weeks, plan.race_date, now);
  if (workouts && workouts.length > 0) {
    const maxGen = Math.max(...workouts.map((w) => Number(w.week_number) || 0));
    if (maxGen > 0) {
      return Math.min(currentWeek, maxGen);
    }
  }
  return currentWeek;
}
