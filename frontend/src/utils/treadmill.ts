// Standard "1% treadmill rule": a 1% incline on a treadmill approximates the
// energy cost of outdoor running, which has wind resistance and terrain
// variation a treadmill belt doesn't reproduce.
export const DEFAULT_TREADMILL_GRADE_PERCENT = 1.0;

// Parses a pace string like "6:00 /km", "6:00/km", or "6:00" into decimal
// minutes per km (e.g. "6:30" -> 6.5). Returns null if unparseable.
export function parsePaceToDecimalMinutes(pace: string | null | undefined): number | null {
  if (!pace) return null;
  const match = pace.match(/(\d+):(\d{1,2})/);
  if (!match) return null;
  const minutes = parseInt(match[1], 10);
  const seconds = parseInt(match[2], 10);
  if (Number.isNaN(minutes) || Number.isNaN(seconds)) return null;
  return minutes + seconds / 60;
}

// Parses a pace string — single or range ("6:30 - 5:45 /km") — into
// [slower, faster] decimal min/km. Mirrors PlanGenerator.parse_pace_range.
export function parsePaceRange(pace: string | null | undefined): [number, number] | null {
  if (!pace) return null;
  const matches = [...pace.matchAll(/(\d+):(\d{1,2})/g)].slice(0, 2);
  if (matches.length === 0) {
    const single = parsePaceToDecimalMinutes(pace);
    return single === null ? null : [single, single];
  }
  const values = matches.map((m) => parseInt(m[1], 10) + parseInt(m[2], 10) / 60);
  if (values.length === 1) values.push(values[0]);
  return [Math.max(values[0], values[1]), Math.min(values[0], values[1])];
}

// "8.2-9.2" (or "8.2" when both ends coincide) — mirrors the backend's
// PlanGenerator._format_range so estimated guides read like stored ones.
function formatRange(a: number, b: number): string {
  const fmt = (v: number) => String(Math.round(v * 10) / 10);
  const low = Math.min(a, b);
  const high = Math.max(a, b);
  return fmt(low) === fmt(high) ? fmt(low) : `${fmt(low)}-${fmt(high)}`;
}

export interface TreadmillSettings {
  speedKph: number;
  inclinePercent: number;
}

// Converts a flat-ground target pace to treadmill speed/incline. Mirrors
// backend/services/training_rules.py's calculate_treadmill_settings — same
// grade-adjusted metabolic model (each 1% incline raises effort ~4.5%, so
// speed is reduced to hold effort constant).
export function calculateTreadmillSettings(
  flatPaceMinPerKm: number,
  gradePercent: number
): TreadmillSettings {
  if (flatPaceMinPerKm <= 0) {
    return { speedKph: 0, inclinePercent: gradePercent };
  }
  const flatSpeedKph = 60 / flatPaceMinPerKm;
  const adjustedSpeedKph = gradePercent > 0 ? flatSpeedKph / (1 + 0.045 * gradePercent) : flatSpeedKph;
  return {
    speedKph: Math.round(adjustedSpeedKph * 10) / 10,
    inclinePercent: Math.round(gradePercent * 10) / 10,
  };
}

export interface TreadmillGuide {
  // Either a computed number (estimated guides) or the backend's range string
  // ("8.1-9.2") passed through verbatim for display.
  speedKph: number | string;
  inclinePercent: number | string;
  estimated: boolean;
  // Where the incline came from when estimated — lets callers explain the
  // number accurately instead of always citing the flat 1% rule, which is
  // only true for the "default" case.
  gradeSource: "ai" | "outdoor-grade" | "default";
}

// The backend stores treadmill settings as range strings ("8.1-9.2" kph,
// "7.3-9.3" %); plans generated before that change still carry numbers.
// Returns the leading number for is-it-set checks, 0 when blank/unparseable.
export function leadingNumber(value: number | string | null | undefined): number {
  if (typeof value === "number") return value;
  if (!value) return 0;
  const n = parseFloat(String(value));
  return Number.isNaN(n) ? 0 : n;
}

// Resolves the treadmill guide to show for a workout: prefers the backend's
// own treadmill_speed/treadmill_incline when both are set (deterministic
// ranges derived from the workout's pace). Otherwise derives one from the
// workout's target pace, preferring this same run's own outdoor grade_percent
// over the flat 1% default — so a trail run with real climbing shows a
// Treadmill Grade that matches its Outdoor Grade, instead of defaulting to a
// flat belt that under-trains the climb. Falls back to the standard 1%
// incline rule only when neither an AI-supplied incline nor an outdoor
// grade_percent exists.
export function getTreadmillGuide(
  targetPace: string | null | undefined,
  aiSpeedKph: number | string,
  aiInclinePercent: number | string,
  outdoorGradePercent?: number | null
): TreadmillGuide | null {
  const speedNum = leadingNumber(aiSpeedKph);
  const inclineNum = leadingNumber(aiInclinePercent);
  if (speedNum > 0 && inclineNum > 0) {
    return { speedKph: aiSpeedKph, inclinePercent: aiInclinePercent, estimated: false, gradeSource: "ai" };
  }

  const pace = parsePaceToDecimalMinutes(targetPace);
  if (pace === null) {
    if (speedNum > 0 || inclineNum > 0) {
      return { speedKph: aiSpeedKph, inclinePercent: aiInclinePercent, estimated: false, gradeSource: "ai" };
    }
    return null;
  }

  const hasOutdoorGrade = !!outdoorGradePercent && outdoorGradePercent > 0;
  const grade = inclineNum > 0 ? inclineNum : hasOutdoorGrade ? outdoorGradePercent! : DEFAULT_TREADMILL_GRADE_PERCENT;
  const gradeSource: TreadmillGuide["gradeSource"] = inclineNum > 0 ? "ai" : hasOutdoorGrade ? "outdoor-grade" : "default";

  // Mirror the backend's range semantics (PlanGenerator.resolve_treadmill_settings):
  // a ±1% incline band around the resolved grade (floored at 1%), and speed
  // derived from both ends of the pace range at the band midpoint.
  const inclineLow = Math.max(1.0, grade - 1.0);
  const inclineHigh = grade + 1.0;
  const inclineMid = (inclineLow + inclineHigh) / 2;
  const paceRange = parsePaceRange(targetPace) ?? [pace, pace];
  const speedLow = calculateTreadmillSettings(paceRange[0], inclineMid).speedKph;
  const speedHigh = calculateTreadmillSettings(paceRange[1], inclineMid).speedKph;
  return {
    speedKph: formatRange(speedLow, speedHigh),
    inclinePercent: formatRange(inclineLow, inclineHigh),
    estimated: true,
    gradeSource,
  };
}
