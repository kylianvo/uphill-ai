// Pure helpers for the Pace Strategy tool (docs/pace-strategy-v2-plan.md Phase 2).

export interface CourseCheckpoint {
  name: string;
  distance_meters: number;
  elevation_meters: number;
  segment_gain_meters: number;
  segment_loss_meters: number;
}

export interface PacedCheckpoint {
  name: string;
  distance_km: number;
  elevation_m: number;
  target_pace: string;
  split_time: string;
  cumulative_time_mins: number;
  flat_equivalent_km: number;
  grade_pct: number;
  effort: "run" | "hike";
  temp_c?: number | null;
  after_sunset?: boolean;
}

/** Parses "5:30", "6", "6.5" or a range like "6:30-5:45" (first value wins) to decimal min/km. */
export function parsePaceToMinutes(pace: string): number | null {
  const first = pace.trim().split(/[-–]/)[0].trim();
  const mmss = first.match(/^(\d{1,2}):([0-5]\d)$/);
  if (mmss) return parseInt(mmss[1], 10) + parseInt(mmss[2], 10) / 60;
  const decimal = first.match(/^\d+(\.\d+)?$/);
  if (decimal) return parseFloat(first);
  return null;
}

export function formatDurationHM(totalMins: number): string {
  const mins = Math.round(totalMins);
  return `${Math.floor(mins / 60)}:${String(mins % 60).padStart(2, "0")}`;
}

export function formatDurationHMS(totalMins: number): string {
  const secs = Math.round(totalMins * 60);
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/**
 * Builds per-km checkpoints for a race picked from the course DB (no GPX).
 * Gain/loss are spread evenly; loss defaults to gain since courses loop or
 * return to the valley. Elevation traces a symmetric out-and-back profile so
 * the chart has a shape (real profiles come from GPX upload).
 */
export function synthesizeCourse(
  distanceKm: number,
  gainM: number,
  lossM: number = gainM,
  baseElevationM: number = 0,
): CourseCheckpoint[] {
  const n = Math.max(1, Math.ceil(distanceKm));
  const checkpoints: CourseCheckpoint[] = [
    {
      name: "Start",
      distance_meters: 0,
      elevation_meters: baseElevationM,
      segment_gain_meters: 0,
      segment_loss_meters: 0,
    },
  ];
  let elevation = baseElevationM;
  // distribute by actual km so totals are preserved on fractional distances
  const gainPerKm = gainM / distanceKm;
  const lossPerKm = lossM / distanceKm;
  for (let km = 1; km <= n; km++) {
    const distM = Math.min(km * 1000, distanceKm * 1000);
    const frac = (distM - checkpoints[km - 1].distance_meters) / 1000;
    elevation += (gainPerKm - lossPerKm) * frac;
    // symmetric bump peaking mid-course, so profiles aren't a flat line
    const bump = Math.sin((Math.min(km, n) / n) * Math.PI) * Math.min(gainM, lossM) * 0.25;
    checkpoints.push({
      name: `KM ${Math.round(distM / 1000)}`,
      distance_meters: distM,
      elevation_meters: Math.round(elevation + bump),
      segment_gain_meters: gainPerKm * frac,
      segment_loss_meters: lossPerKm * frac,
    });
  }
  return checkpoints;
}

/**
 * Clock ETAs per checkpoint. Rest minutes taken AT a checkpoint delay all
 * later arrivals but not that checkpoint's own. Without a start time,
 * returns elapsed h:mm durations (rest included).
 */
export function addClockEtas(
  paced: { cumulative_time_mins: number }[],
  restMins: number[],
  startClock?: string,
): string[] {
  let startOffset: number | null = null;
  if (startClock) {
    const m = startClock.match(/^(\d{1,2}):(\d{2})$/);
    if (m) startOffset = parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
  }
  let restSoFar = 0;
  return paced.map((cp, idx) => {
    const arrival = cp.cumulative_time_mins + restSoFar;
    restSoFar += restMins[idx] || 0;
    if (startOffset === null) return formatDurationHM(arrival);
    const clock = Math.round(startOffset + arrival) % (24 * 60);
    return `${String(Math.floor(clock / 60)).padStart(2, "0")}:${String(clock % 60).padStart(2, "0")}`;
  });
}

/** Finish-time slider range: base flat paces 3.5–12 min/km over a rough flat-equivalent distance. */
export function sliderBoundsMins(distanceKm: number, gainM: number): { min: number; max: number; step: number } {
  const flatEqKm = distanceKm + gainM / 100;
  return {
    min: Math.floor(flatEqKm * 3.5),
    max: Math.ceil(flatEqKm * 12),
    step: 5,
  };
}
