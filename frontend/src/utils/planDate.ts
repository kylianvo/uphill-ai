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
