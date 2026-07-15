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
  rain_mm?: number | null;
  after_sunset?: boolean;
  energy_kcal?: number;
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
  intervalKm: number = 1,
): CourseCheckpoint[] {
  const n = Math.max(1, Math.ceil(distanceKm / intervalKm));
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
  for (let i = 1; i <= n; i++) {
    const distM = Math.min(i * intervalKm * 1000, distanceKm * 1000);
    const frac = (distM - checkpoints[i - 1].distance_meters) / 1000;
    elevation += (gainPerKm - lossPerKm) * frac;
    // symmetric bump peaking mid-course, so profiles aren't a flat line
    const bump = Math.sin((Math.min(i, n) / n) * Math.PI) * Math.min(gainM, lossM) * 0.25;
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

/** Parses "9:10:58" or "2:30" race times to decimal minutes. */
export function parseDurationToMinutes(time: string): number | null {
  const m = time.trim().match(/^(\d{1,2}):([0-5]\d)(?::([0-5]\d))?$/);
  if (!m) return null;
  return parseInt(m[1], 10) * 60 + parseInt(m[2], 10) + (m[3] ? parseInt(m[3], 10) / 60 : 0);
}

export interface PercentileSet {
  p10?: string;
  p25?: string;
  p50?: string;
  p75?: string;
  p90?: string;
}

/** Hand-curated percentile anchors parsed to {q: percent, mins}, sorted by q. */
export function percentilePoints(ps: PercentileSet): { q: number; mins: number }[] {
  return Object.entries(ps)
    .map(([key, time]) => ({ q: parseInt(key.slice(1), 10), mins: time ? parseDurationToMinutes(time) : null }))
    .filter((p): p is { q: number; mins: number } => !Number.isNaN(p.q) && p.mins !== null)
    .sort((a, b) => a.q - b.q);
}

export interface FieldAnchor {
  q: number; // percent of the group's field at or ahead of this time
  mins: number;
}

/**
 * Combines every verified anchor a race-year offers into one sorted list:
 * winner (rank 1), top-N rank times converted to percentiles via the group's
 * finisher count, and the pN percentiles. Anchors that would break
 * monotonicity (bad data) are dropped rather than reordered.
 */
export function fieldAnchors(opts: {
  percentiles?: PercentileSet;
  topTimes?: Record<string, string>;
  winner?: string | null;
  finishers?: number | null;
}): FieldAnchor[] {
  const raw: FieldAnchor[] = [];
  const winnerMins = opts.winner ? parseDurationToMinutes(opts.winner) : null;
  if (winnerMins !== null) {
    raw.push({ q: opts.finishers ? 100 / opts.finishers : 0, mins: winnerMins });
  }
  if (opts.finishers) {
    for (const [key, time] of Object.entries(opts.topTimes || {})) {
      const rank = parseInt(key.replace(/^top/, ""), 10);
      const mins = time ? parseDurationToMinutes(time) : null;
      if (!Number.isNaN(rank) && rank > 0 && mins !== null) {
        raw.push({ q: (100 * rank) / opts.finishers, mins });
      }
    }
  }
  raw.push(...percentilePoints(opts.percentiles || {}));
  raw.sort((a, b) => a.q - b.q);

  const anchors: FieldAnchor[] = [];
  for (const a of raw) {
    const prev = anchors[anchors.length - 1];
    if (!prev || (a.q > prev.q && a.mins > prev.mins)) anchors.push(a);
  }
  return anchors;
}

/** Where a finish time lands among sorted anchors: piecewise-linear, clamped. */
export function percentileForAnchors(
  anchors: FieldAnchor[],
  timeMins: number,
): { pct: number; clamped: "fast" | "slow" | null } | null {
  if (anchors.length < 2) return null;
  if (timeMins <= anchors[0].mins) {
    return timeMins === anchors[0].mins
      ? { pct: anchors[0].q, clamped: null }
      : { pct: anchors[0].q, clamped: "fast" };
  }
  const last = anchors[anchors.length - 1];
  if (timeMins >= last.mins) {
    return timeMins === last.mins ? { pct: last.q, clamped: null } : { pct: last.q, clamped: "slow" };
  }
  for (let i = 1; i < anchors.length; i++) {
    if (timeMins <= anchors[i].mins) {
      const a = anchors[i - 1];
      const b = anchors[i];
      const frac = (timeMins - a.mins) / (b.mins - a.mins);
      return { pct: a.q + frac * (b.q - a.q), clamped: null };
    }
  }
  return null;
}

/**
 * Where a finish time lands in the field: linear interpolation between the
 * verified percentile anchors, clamped at the ends (never extrapolated).
 * A winner time, when given, anchors the fast end at 0%.
 */
export function percentileForTime(
  ps: PercentileSet,
  timeMins: number,
  winnerMins?: number | null,
): { pct: number; clamped: "fast" | "slow" | null } | null {
  const pts = percentilePoints(ps);
  if (pts.length < 2) return null;
  const anchors = winnerMins && winnerMins < pts[0].mins ? [{ q: 0, mins: winnerMins }, ...pts] : pts;
  return percentileForAnchors(anchors, timeMins);
}

/** Maps a forecast temperature to the Nutrition Lab's weather buckets. */
export function tempBucket(tempC: number | null | undefined): "cool" | "moderate" | "hot" {
  if (tempC == null) return "moderate";
  if (tempC < 12) return "cool";
  if (tempC > 25) return "hot";
  return "moderate";
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
