// The run days an ultra needs before its weekly time fits (backend goal_feasibility; docs/plan-rules.md R-W3).
// Guidance only: the runner can still create the plan.
export function recommendedRunDays(distanceKm: number | null | undefined, days: number): number | null {
  const km = distanceKm || 0;
  const min = km >= 90 ? 5 : km >= 45 ? 4 : 0;
  return days < min ? min : null;
}
