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

export interface TreadmillGuide extends TreadmillSettings {
  estimated: boolean;
}

// Resolves the treadmill guide to show for a workout: prefers the AI's own
// treadmill_speed/treadmill_incline when both are set (e.g. a course-
// elevation-specific gym session), otherwise derives one from the workout's
// target pace and the standard 1% incline rule, so the Treadmill tab always
// shows an actionable Speed/Grade instead of going blank.
export function getTreadmillGuide(
  targetPace: string | null | undefined,
  aiSpeedKph: number,
  aiInclinePercent: number
): TreadmillGuide | null {
  if (aiSpeedKph > 0 && aiInclinePercent > 0) {
    return { speedKph: aiSpeedKph, inclinePercent: aiInclinePercent, estimated: false };
  }

  const pace = parsePaceToDecimalMinutes(targetPace);
  if (pace === null) {
    if (aiSpeedKph > 0 || aiInclinePercent > 0) {
      return { speedKph: aiSpeedKph, inclinePercent: aiInclinePercent, estimated: false };
    }
    return null;
  }

  const grade = aiInclinePercent > 0 ? aiInclinePercent : DEFAULT_TREADMILL_GRADE_PERCENT;
  const settings = calculateTreadmillSettings(pace, grade);
  return { ...settings, estimated: true };
}
