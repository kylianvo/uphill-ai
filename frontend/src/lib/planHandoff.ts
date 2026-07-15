export function minsToHms(totalMins: number): { h: string; m: string; s: string } {
  const totalSecs = Math.round(totalMins * 60);
  const h = Math.floor(totalSecs / 3600);
  const m = Math.floor((totalSecs % 3600) / 60);
  const s = totalSecs % 60;
  return { h: String(h), m: String(m), s: String(s) };
}

export function isTaperPhase(phase: string | null | undefined): boolean {
  return !!phase && phase.toLowerCase().includes("taper");
}

export interface PaceHandoffPayload {
  race_name: string;
  distance_km?: number;
  target_time_mins?: number;
}

export function buildPaceHandoffFromPlan(plan: {
  race_name: string;
  goal_type: string;
  course_distance_km?: number | null;
  target_time_hours?: number | null;
}): PaceHandoffPayload {
  const payload: PaceHandoffPayload = { race_name: plan.race_name };
  if (plan.course_distance_km) payload.distance_km = plan.course_distance_km;
  if (plan.goal_type === "time" && plan.target_time_hours) {
    payload.target_time_mins = Math.round(plan.target_time_hours * 60);
  }
  return payload;
}
